from __future__ import annotations

import os
import threading
import time
import unittest
from contextlib import ExitStack
from dataclasses import dataclass
from unittest.mock import patch

from provider.app import OcrRuntime, RuntimeAdmissionController
from provider.config import Settings


class RuntimeAdmissionControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_stack = ExitStack()
        env = {
            "SERVICE_NAME": "ocr-provider",
            "OCR_PROVIDER": "rapidocr",
            "OCR_MODEL": "rapidocr:ch_sim+en",
            "OCR_LANGUAGES": "ch_sim,en",
            "OCR_DEVICE": "cuda",
            "OCR_MAX_CONCURRENCY": "4",
            "OCR_QUEUE_TIMEOUT_SECONDS": "1.0",
            "OCR_QUEUE_POLL_SECONDS": "0.05",
            "OCR_GPU_MIN_FREE_VRAM_MB": "4096",
            "OCR_GPU_PER_REQUEST_VRAM_MB": "3072",
        }
        for key, value in env.items():
            self._env_stack.enter_context(patch.dict(os.environ, {key: value}))

    def tearDown(self) -> None:
        self._env_stack.close()

    def test_status_scales_dynamic_limit_from_free_vram(self) -> None:
        controller = RuntimeAdmissionController(Settings.from_env(), "cuda")

        with patch.object(controller, "_probe_cuda_memory_mb", return_value=(9000, 32607)):
            status = controller.status()

        self.assertEqual(status["dynamic_limit"], 1)
        self.assertEqual(status["free_vram_mb"], 9000)
        self.assertEqual(status["total_vram_mb"], 32607)

    def test_waiting_requests_queue_until_capacity_frees(self) -> None:
        controller = RuntimeAdmissionController(Settings.from_env(), "cuda")
        phase = {"value": "limited"}
        started = threading.Event()
        second_finished = threading.Event()
        observed_active: list[int] = []
        observed_queued: list[int] = []

        def fake_probe() -> tuple[int, int]:
            if phase["value"] == "limited":
                return (7200, 32607)
            return (27442, 32607)

        with patch.object(controller, "_probe_cuda_memory_mb", side_effect=fake_probe):
            with controller.acquire():
                def worker() -> None:
                    started.set()
                    with controller.acquire():
                        snapshot = controller.status()
                        observed_active.append(int(snapshot["active_requests"]))
                        observed_queued.append(int(snapshot["queued_requests"]))
                        second_finished.set()

                thread = threading.Thread(target=worker)
                thread.start()
                self.assertTrue(started.wait(timeout=0.2))
                time.sleep(0.15)
                queued_snapshot = controller.status()
                self.assertEqual(queued_snapshot["dynamic_limit"], 1)
                self.assertEqual(queued_snapshot["active_requests"], 1)
                self.assertEqual(queued_snapshot["queued_requests"], 1)
                phase["value"] = "open"
            thread.join(timeout=1)

        self.assertFalse(thread.is_alive())
        self.assertTrue(second_finished.is_set())
        self.assertEqual(observed_active, [1])
        self.assertEqual(observed_queued, [0])

@dataclass
class FakeEngine:
    provider_name: str
    model_id: str
    device_name: str

    def ocr_image(self, data: bytes) -> object:
        return object()


class OcrRuntimeIdleOffloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_stack = ExitStack()
        env = {
            "SERVICE_NAME": "ocr-provider",
            "OCR_PROVIDER": "rapidocr",
            "OCR_MODEL": "rapidocr:ch_sim+en",
            "OCR_LANGUAGES": "ch_sim,en",
            "OCR_DEVICE": "cuda",
            "OCR_MAX_CONCURRENCY": "4",
            "OCR_QUEUE_TIMEOUT_SECONDS": "1.0",
            "OCR_QUEUE_POLL_SECONDS": "0.05",
            "OCR_IDLE_OFFLOAD_SECONDS": "0.05",
            "OCR_IDLE_OFFLOAD_POLL_SECONDS": "1",
            "OCR_GPU_MIN_FREE_VRAM_MB": "4096",
            "OCR_GPU_PER_REQUEST_VRAM_MB": "3072",
        }
        for key, value in env.items():
            self._env_stack.enter_context(patch.dict(os.environ, {key: value}))

    def tearDown(self) -> None:
        self._env_stack.close()

    def test_idle_runtime_offloads_and_reloads(self) -> None:
        build_calls: list[str] = []

        def fake_build_engine(settings: Settings, ocr_device_override: str | None = None) -> FakeEngine:
            device = ocr_device_override or "cuda"
            build_calls.append(device)
            return FakeEngine(provider_name="rapidocr", model_id=settings.model_id, device_name=device)

        with patch("provider.app.build_engine", side_effect=fake_build_engine):
            runtime = OcrRuntime(Settings.from_env())
            try:
                runtime._last_request_finished_at -= 1
                runtime._maybe_offload_to_cpu()
                status = runtime.runtime_status()
                self.assertEqual(status["engine_state"], "offloaded")
                self.assertEqual(status["loaded_device"], "cpu")

                with patch.object(runtime._admission, "_probe_cuda_memory_mb", return_value=(27442, 32607)):
                    with runtime.request_slot():
                        hot_status = runtime.runtime_status()
                        self.assertEqual(hot_status["engine_state"], "hot")
                        self.assertEqual(hot_status["loaded_device"], "cuda")
            finally:
                runtime.close()

        self.assertEqual(build_calls, ["cuda", "cpu", "cuda"])


if __name__ == "__main__":
    unittest.main()
