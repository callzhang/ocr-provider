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
        return "cpu"
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
    tesseract_cmd: str | None

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
            ocr_device=(os.getenv("OCR_DEVICE") or _legacy_device_default()).strip().lower(),
            paragraph=_env_bool("OCR_PARAGRAPH", True),
            model_storage_dir=Path(os.getenv("OCR_MODEL_STORAGE_DIR") or os.getenv("MODEL_STORAGE_DIR") or "./runtime-cache/ocr"),
            render_scale=float(os.getenv("PDF_RENDER_SCALE", "2.0")),
            tesseract_cmd=os.getenv("TESSERACT_CMD") or None,
        )
