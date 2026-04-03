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


def _env_int(name: str, default: str | None = None) -> int | None:
    value = os.getenv(name, default)
    if value in (None, ""):
        return None
    return int(value)


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


@dataclass(frozen=True)
class Settings:
    service_name: str
    model_id: str
    model_alias: str | None
    api_key: str | None
    ocr_languages: tuple[str, ...]
    use_gpu: bool
    paragraph: bool
    model_storage_dir: Path
    render_scale: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            service_name=os.getenv("SERVICE_NAME", "ocr-provider"),
            model_id=os.getenv("MODEL_ID", "easyocr:ch_sim+en"),
            model_alias=os.getenv("MODEL_ALIAS") or None,
            api_key=os.getenv("API_KEY") or None,
            ocr_languages=_env_languages("OCR_LANGUAGES", ("ch_sim", "en")),
            use_gpu=_env_bool("USE_GPU", True),
            paragraph=_env_bool("OCR_PARAGRAPH", True),
            model_storage_dir=Path(os.getenv("MODEL_STORAGE_DIR", "./runtime-cache/easyocr-zh-en")),
            render_scale=float(os.getenv("PDF_RENDER_SCALE", "2.0")),
        )
