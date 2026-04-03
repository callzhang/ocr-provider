from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_languages(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    raw = value.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = [part.strip() for part in raw.split(",") if part.strip()]
        if isinstance(parsed, list):
            return tuple(str(item).strip() for item in parsed if str(item).strip())
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _legacy_device_default() -> str:
    if "USE_GPU" not in os.environ:
        return "auto"
    return "cuda" if _env_bool("USE_GPU", False) else "cpu"


@dataclass(frozen=True)
class Settings:
    service_name: str
    ocr_provider: str
    model_id: str
    model_alias: str | None
    api_key: str | None
    ocr_languages: tuple[str, ...]
    ocr_device: str
    paragraph: bool
    model_storage_dir: Path
    render_scale: float
    max_concurrency: int
    queue_timeout_seconds: float
    queue_poll_seconds: float
    gpu_min_free_vram_mb: int
    gpu_per_request_vram_mb: int
    tesseract_cmd: str | None
    paddle_text_detection_model_name: str | None
    paddle_text_recognition_model_name: str | None
    paddle_lang: str | None
    paddle_use_doc_orientation_classify: bool
    paddle_use_doc_unwarping: bool
    paddle_use_textline_orientation: bool
    paddle_disable_model_source_check: bool

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("OCR_PROVIDER", "").strip() or ""
        model_id = (
            os.getenv("OCR_MODEL")
            or os.getenv("OCR_MODEL_ID")
            or os.getenv("MODEL_ID")
            or "rapidocr:ch_sim+en"
        )
        resolved_provider = provider or str(model_id).split(":", 1)[0]
        return cls(
            service_name=os.getenv("SERVICE_NAME", "ocr-provider"),
            ocr_provider=resolved_provider,
            model_id=model_id,
            model_alias=os.getenv("OCR_MODEL_ALIAS") or os.getenv("MODEL_ALIAS") or None,
            api_key=os.getenv("API_KEY") or None,
            ocr_languages=_env_languages("OCR_LANGUAGES", ("ch_sim", "en")),
            ocr_device=_normalize_device(os.getenv("OCR_DEVICE") or _legacy_device_default()),
            paragraph=_env_bool("OCR_PARAGRAPH", True),
            model_storage_dir=Path(os.getenv("OCR_MODEL_STORAGE_DIR") or os.getenv("MODEL_STORAGE_DIR") or "./runtime-cache/ocr"),
            render_scale=float(os.getenv("PDF_RENDER_SCALE", "2.0")),
            max_concurrency=max(1, int(os.getenv("OCR_MAX_CONCURRENCY", "4"))),
            queue_timeout_seconds=max(0.1, float(os.getenv("OCR_QUEUE_TIMEOUT_SECONDS", "15"))),
            queue_poll_seconds=max(0.05, float(os.getenv("OCR_QUEUE_POLL_SECONDS", "0.2"))),
            gpu_min_free_vram_mb=max(0, int(os.getenv("OCR_GPU_MIN_FREE_VRAM_MB", "4096"))),
            gpu_per_request_vram_mb=max(1, int(os.getenv("OCR_GPU_PER_REQUEST_VRAM_MB", "3072"))),
            tesseract_cmd=os.getenv("TESSERACT_CMD") or None,
            paddle_text_detection_model_name=os.getenv("PADDLE_OCR_TEXT_DETECTION_MODEL_NAME") or None,
            paddle_text_recognition_model_name=os.getenv("PADDLE_OCR_TEXT_RECOGNITION_MODEL_NAME") or None,
            paddle_lang=os.getenv("PADDLE_OCR_LANG") or None,
            paddle_use_doc_orientation_classify=_env_bool("PADDLE_OCR_USE_DOC_ORIENTATION_CLASSIFY", False),
            paddle_use_doc_unwarping=_env_bool("PADDLE_OCR_USE_DOC_UNWARPING", False),
            paddle_use_textline_orientation=_env_bool("PADDLE_OCR_USE_TEXTLINE_ORIENTATION", False),
            paddle_disable_model_source_check=_env_bool("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", True),
        )


def _normalize_device(value: str) -> str:
    normalized = str(value or "cpu").strip().lower()
    aliases = {
        "gpu": "cuda",
        "apple": "coreml",
        "apple-gpu": "coreml",
        "metal": "coreml",
    }
    return aliases.get(normalized, normalized)
