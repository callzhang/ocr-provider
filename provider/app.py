from __future__ import annotations

import base64
from contextlib import contextmanager
import gc
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Any, Literal

import fitz
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from provider.config import Settings
from provider.engines import EngineOcrResult, OcrEngine, build_engine

log = logging.getLogger("ocr_provider")
logging.basicConfig(level="INFO")


class OcrInput(BaseModel):
    source_id: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    data_base64: str = Field(min_length=1)
    page_numbers: list[int] | None = None


class OcrRequest(BaseModel):
    model: str | None = None
    languages: list[str] | None = None
    inputs: list[OcrInput] = Field(min_length=1)


class OcrPageResult(BaseModel):
    page_number: int
    text: str
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)


class OcrItem(BaseModel):
    source_id: str
    text: str = ""
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)
    pages: list[OcrPageResult] = Field(default_factory=list)


class OcrResponse(BaseModel):
    object: Literal["list"] = "list"
    model: str
    data: list[OcrItem]


class ModelInfo(BaseModel):
    id: str
    object: Literal["model"] = "model"
    owned_by: str = "stardust"


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelInfo]


class OcrRuntime:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine_lock = threading.Condition()
        self._engine: OcrEngine = build_engine(settings)
        self.device_name = self._engine.device_name
        self._admission = RuntimeAdmissionController(settings, self.device_name)
        self._preferred_loaded_device = self.device_name
        self._inflight_requests = 0
        self._reload_in_progress = False
        self._engine_state = "hot"
        self._last_request_finished_at = time.monotonic()
        self._last_offloaded_at: float | None = None
        self._idle_offload_enabled = self.device_name == "cuda" and settings.idle_offload_seconds > 0
        self._shutdown_event = threading.Event()
        self._idle_offload_thread: threading.Thread | None = None
        if self._idle_offload_enabled:
            self._idle_offload_thread = threading.Thread(
                target=self._idle_offload_loop,
                name="ocr-idle-offload",
                daemon=True,
            )
            self._idle_offload_thread.start()

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        return self._engine.ocr_image(data)

    def ocr_pdf(self, data: bytes, page_numbers: list[int] | None) -> list[OcrPageResult]:
        pdf = fitz.open(stream=data, filetype="pdf")
        requested = page_numbers or list(range(1, pdf.page_count + 1))
        page_results: list[OcrPageResult] = []
        matrix = fitz.Matrix(self._settings.render_scale, self._settings.render_scale)
        for page_number in requested:
            if page_number < 1 or page_number > pdf.page_count:
                page_results.append(
                    OcrPageResult(
                        page_number=page_number,
                        text="",
                        warnings=[f"page {page_number} is out of range for PDF with {pdf.page_count} pages"],
                    )
                )
                continue
            page = pdf.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            result = self.ocr_image(pixmap.tobytes("png"))
            page_results.append(
                OcrPageResult(
                    page_number=page_number,
                    text=result.text,
                    confidence=result.confidence,
                    warnings=result.warnings or ([] if result.text else [f"no text recognized on page {page_number}"]),
                )
            )
        return page_results

    @contextmanager
    def request_slot(self) -> Any:
        with self._admission.acquire():
            self._begin_request()
            try:
                yield
            finally:
                self._finish_request()

    def admission_status(self) -> dict[str, Any]:
        return self._admission.status()

    def runtime_status(self) -> dict[str, Any]:
        with self._engine_lock:
            idle_for = max(0.0, time.monotonic() - self._last_request_finished_at)
            offloaded_for = None
            if self._last_offloaded_at is not None:
                offloaded_for = max(0.0, time.monotonic() - self._last_offloaded_at)
            return {
                "loaded_device": self.device_name,
                "preferred_device": self._preferred_loaded_device,
                "engine_state": self._engine_state,
                "idle_offload_enabled": self._idle_offload_enabled,
                "idle_offload_seconds": self._settings.idle_offload_seconds if self._idle_offload_enabled else None,
                "idle_offload_poll_seconds": (
                    self._settings.idle_offload_poll_seconds if self._idle_offload_enabled else None
                ),
                "inflight_requests": self._inflight_requests,
                "idle_for_seconds": round(idle_for, 3),
                "offloaded_for_seconds": round(offloaded_for, 3) if offloaded_for is not None else None,
                "reload_in_progress": self._reload_in_progress,
            }

    def close(self) -> None:
        self._shutdown_event.set()
        if self._idle_offload_thread is not None:
            self._idle_offload_thread.join(timeout=1)

    def _begin_request(self) -> None:
        with self._engine_lock:
            self._inflight_requests += 1
            self._engine_lock.notify_all()
        try:
            self._ensure_hot_engine()
        except Exception:
            self._finish_request()
            raise

    def _finish_request(self) -> None:
        with self._engine_lock:
            self._inflight_requests = max(0, self._inflight_requests - 1)
            self._last_request_finished_at = time.monotonic()
            self._engine_lock.notify_all()

    def _ensure_hot_engine(self) -> None:
        if not self._idle_offload_enabled:
            return
        with self._engine_lock:
            while self._reload_in_progress:
                self._engine_lock.wait()
            if self._engine_state == "hot":
                return
            self._reload_in_progress = True
        try:
            self._swap_engine(build_engine(self._settings), engine_state="hot")
        finally:
            with self._engine_lock:
                self._reload_in_progress = False
                self._engine_lock.notify_all()

    def _idle_offload_loop(self) -> None:
        while not self._shutdown_event.wait(self._settings.idle_offload_poll_seconds):
            self._maybe_offload_to_cpu()

    def _maybe_offload_to_cpu(self) -> None:
        if not self._idle_offload_enabled:
            return
        with self._engine_lock:
            if self._reload_in_progress or self._engine_state == "offloaded" or self._inflight_requests > 0:
                return
            idle_for = time.monotonic() - self._last_request_finished_at
            if idle_for < self._settings.idle_offload_seconds:
                return
            self._reload_in_progress = True
        try:
            self._swap_engine(build_engine(self._settings, ocr_device_override="cpu"), engine_state="offloaded")
        finally:
            with self._engine_lock:
                self._reload_in_progress = False
                self._engine_lock.notify_all()

    def _swap_engine(self, next_engine: OcrEngine, engine_state: str) -> None:
        with self._engine_lock:
            old_engine = self._engine
            self._engine = next_engine
            self.device_name = next_engine.device_name
            self._engine_state = engine_state
            if engine_state == "offloaded":
                self._last_offloaded_at = time.monotonic()
            else:
                self._last_offloaded_at = None
        if old_engine is not next_engine:
            del old_engine
            gc.collect()
            _release_accelerator_cache()


class RuntimeBusyError(RuntimeError):
    def __init__(self, snapshot: dict[str, Any]) -> None:
        super().__init__("OCR runtime is busy")
        self.snapshot = snapshot


class RuntimeAdmissionController:
    def __init__(self, settings: Settings, device_name: str) -> None:
        self._settings = settings
        self._device_name = device_name
        self._condition = threading.Condition()
        self._active_requests = 0
        self._queued_requests = 0
        self._last_probe_error: str | None = None

    @contextmanager
    def acquire(self) -> Any:
        deadline = time.monotonic() + self._settings.queue_timeout_seconds
        acquired = False
        with self._condition:
            self._queued_requests += 1
            try:
                while True:
                    snapshot = self._snapshot_locked()
                    dynamic_limit = int(snapshot["dynamic_limit"])
                    if dynamic_limit > 0 and self._active_requests < dynamic_limit:
                        self._active_requests += 1
                        self._queued_requests -= 1
                        acquired = True
                        break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeBusyError(snapshot)
                    self._condition.wait(timeout=min(self._settings.queue_poll_seconds, remaining))
            finally:
                if not acquired:
                    self._queued_requests -= 1
        try:
            yield
        finally:
            with self._condition:
                self._active_requests = max(0, self._active_requests - 1)
                self._condition.notify_all()

    def status(self) -> dict[str, Any]:
        with self._condition:
            return self._snapshot_locked()

    def _snapshot_locked(self) -> dict[str, Any]:
        free_vram_mb: int | None = None
        total_vram_mb: int | None = None
        dynamic_limit = self._settings.max_concurrency
        if self._device_name == "cuda":
            free_vram_mb, total_vram_mb = self._probe_cuda_memory_mb()
            if free_vram_mb is None:
                dynamic_limit = 1
            else:
                headroom_mb = free_vram_mb - self._settings.gpu_min_free_vram_mb
                dynamic_limit = min(
                    self._settings.max_concurrency,
                    max(0, headroom_mb // self._settings.gpu_per_request_vram_mb),
                )
        return {
            "device": self._device_name,
            "active_requests": self._active_requests,
            "queued_requests": self._queued_requests,
            "max_concurrency": self._settings.max_concurrency,
            "dynamic_limit": dynamic_limit,
            "queue_timeout_seconds": self._settings.queue_timeout_seconds,
            "gpu_min_free_vram_mb": self._settings.gpu_min_free_vram_mb if self._device_name == "cuda" else None,
            "gpu_per_request_vram_mb": self._settings.gpu_per_request_vram_mb if self._device_name == "cuda" else None,
            "free_vram_mb": free_vram_mb,
            "total_vram_mb": total_vram_mb,
            "last_probe_error": self._last_probe_error,
        }

    def _probe_cuda_memory_mb(self) -> tuple[int | None, int | None]:
        command = [
            "nvidia-smi",
            "--query-gpu=memory.free,memory.total",
            "--format=csv,noheader,nounits",
        ]
        gpu_index = self._resolve_gpu_index()
        if gpu_index is not None:
            command.insert(1, f"--id={gpu_index}")
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception as exc:
            self._last_probe_error = repr(exc)
            return None, None
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            self._last_probe_error = "nvidia-smi returned no rows"
            return None, None
        try:
            free_raw, total_raw = [part.strip() for part in lines[0].split(",", 1)]
            free_vram_mb = int(free_raw)
            total_vram_mb = int(total_raw)
        except Exception as exc:
            self._last_probe_error = f"failed to parse nvidia-smi output: {exc!r}"
            return None, None
        self._last_probe_error = None
        return free_vram_mb, total_vram_mb

    @staticmethod
    def _resolve_gpu_index() -> str | None:
        visible = os.getenv("CUDA_VISIBLE_DEVICES", "").strip()
        if not visible:
            return None
        first = visible.split(",", 1)[0].strip()
        if first.isdigit():
            return first
        return None


def _require_api_key(settings: Settings, authorization: str | None) -> None:
    if not settings.api_key:
        return
    expected = f"Bearer {settings.api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


def create_app(settings: Settings | None = None, runtime: OcrRuntime | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_runtime = runtime or OcrRuntime(resolved_settings)
    app = FastAPI(title="OCR Provider", version="0.2.0")

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "service": resolved_settings.service_name,
            "provider": resolved_settings.ocr_provider,
            "model": resolved_settings.model_id,
            "languages": list(resolved_settings.ocr_languages),
            "device": resolved_runtime.device_name,
            "admission": resolved_runtime.admission_status(),
            "runtime": resolved_runtime.runtime_status(),
        }

    @app.on_event("shutdown")
    def shutdown_runtime() -> None:
        resolved_runtime.close()

    @app.get("/v1/models", response_model=ModelList)
    def list_models() -> ModelList:
        model_ids = [resolved_settings.model_id]
        if resolved_settings.model_alias:
            model_ids.append(resolved_settings.model_alias)
        return ModelList(data=[ModelInfo(id=model_id) for model_id in model_ids])

    @app.post("/v1/ocr", response_model=OcrResponse)
    def ocr(req: OcrRequest, authorization: str | None = Header(default=None)) -> OcrResponse:
        _require_api_key(resolved_settings, authorization)
        languages = req.languages or list(resolved_settings.ocr_languages)
        if tuple(languages) != resolved_settings.ocr_languages:
            log.info("request languages=%s differ from runtime default=%s", languages, resolved_settings.ocr_languages)

        try:
            with resolved_runtime.request_slot():
                items: list[OcrItem] = []
                for item in req.inputs:
                    data = base64.b64decode(item.data_base64)
                    mime_type = item.mime_type.lower()
                    if mime_type == "application/pdf":
                        pages = resolved_runtime.ocr_pdf(data, item.page_numbers)
                        joined = "\n\n".join(page.text for page in pages if page.text)
                        confidences = [page.confidence for page in pages if page.confidence is not None]
                        confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
                        items.append(
                            OcrItem(
                                source_id=item.source_id,
                                text=joined,
                                confidence=confidence,
                                warnings=[warning for page in pages for warning in page.warnings],
                                pages=pages,
                            )
                        )
                        continue
                    result = resolved_runtime.ocr_image(data)
                    items.append(
                        OcrItem(
                            source_id=item.source_id,
                            text=result.text,
                            confidence=result.confidence,
                            warnings=result.warnings or ([] if result.text else ["no text recognized"]),
                        )
                    )
        except RuntimeBusyError as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "OCR_RUNTIME_BUSY",
                    "message": "OCR runtime admission timed out while waiting for free GPU capacity",
                    "admission": exc.snapshot,
                },
            ) from exc

        return OcrResponse(model=req.model or resolved_settings.model_id, data=items)

    return app


app = create_app()


def _release_accelerator_cache() -> None:
    torch = sys.modules.get("torch")
    if torch is None:
        return
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
        except Exception:
            log.exception("failed to empty torch CUDA cache after OCR engine swap")
