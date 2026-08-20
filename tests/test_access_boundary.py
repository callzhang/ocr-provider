from __future__ import annotations

import base64
from contextlib import contextmanager
import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from provider.app import create_app
from provider.config import Settings
from provider.engines import EngineOcrResult


def _settings() -> Settings:
    return Settings(
        service_name="ocr-provider",
        ocr_provider="rapidocr",
        model_id="rapidocr:ch_sim+en",
        model_alias="rapidocr-zh-en",
        ocr_languages=("ch_sim", "en"),
        ocr_device="cpu",
        paragraph=True,
        model_storage_dir=Path("runtime-cache/ocr"),
        render_scale=2.0,
        max_concurrency=4,
        queue_timeout_seconds=15.0,
        queue_poll_seconds=0.2,
        idle_offload_seconds=1800.0,
        idle_offload_poll_seconds=30.0,
        gpu_min_free_vram_mb=4096,
        gpu_per_request_vram_mb=3072,
        tesseract_cmd=None,
        paddle_text_detection_model_name=None,
        paddle_text_recognition_model_name=None,
        paddle_lang=None,
        paddle_use_doc_orientation_classify=False,
        paddle_use_doc_unwarping=False,
        paddle_use_textline_orientation=False,
        paddle_disable_model_source_check=True,
    )


class FakeRuntime:
    device_name = "cpu"

    @contextmanager
    def request_slot(self):
        yield

    def ocr_image(self, _data: bytes) -> EngineOcrResult:
        return EngineOcrResult(text="recognized", confidence=0.99)

    def admission_status(self) -> dict[str, object]:
        return {}

    def runtime_status(self) -> dict[str, object]:
        return {}

    def close(self) -> None:
        return None


def test_origin_accepts_request_without_legacy_bearer_key() -> None:
    client = TestClient(create_app(settings=_settings(), runtime=FakeRuntime()))

    response = client.post(
        "/v1/ocr",
        json={
            "inputs": [
                {
                    "source_id": "image",
                    "mime_type": "image/png",
                    "data_base64": base64.b64encode(b"image").decode("ascii"),
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["text"] == "recognized"


def test_legacy_api_key_environment_is_not_application_configuration() -> None:
    with patch.dict(os.environ, {"API_KEY": "legacy-secret"}, clear=True):
        settings = Settings.from_env()

    assert not hasattr(settings, "api_key")
