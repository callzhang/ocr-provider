from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from PIL import Image

from provider.config import Settings

log = logging.getLogger("ocr_provider")


@dataclass
class EngineOcrResult:
    text: str
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)


class OcrEngine(Protocol):
    provider_name: str
    model_id: str
    device_name: str

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        ...


def build_engine(settings: Settings) -> OcrEngine:
    provider = settings.ocr_provider.strip().lower()
    if provider == "easyocr":
        return EasyOcrEngine(settings)
    if provider == "rapidocr":
        return RapidOcrEngine(settings)
    if provider == "tesseract":
        return TesseractOcrEngine(settings)
    raise ValueError(f"Unsupported OCR provider: {settings.ocr_provider}")


class BaseImageEngine:
    provider_name: str
    model_id: str
    device_name: str

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.provider_name = settings.ocr_provider
        self.model_id = settings.model_id
        self.device_name = "cpu"

    @staticmethod
    def _image_from_bytes(data: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        return np.asarray(image)


class EasyOcrEngine(BaseImageEngine):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        import torch
        import easyocr

        settings.model_storage_dir.mkdir(parents=True, exist_ok=True)
        wants_cuda = settings.ocr_device in {"cuda", "gpu"} or (
            settings.ocr_device == "auto" and torch.cuda.is_available()
        )
        self._reader = easyocr.Reader(
            list(settings.ocr_languages),
            gpu=wants_cuda,
            model_storage_directory=str(settings.model_storage_dir),
            user_network_directory=str(settings.model_storage_dir / "user_network"),
            download_enabled=True,
        )
        self.device_name = "cuda" if wants_cuda else "cpu"

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        results = self._reader.readtext(
            self._image_from_bytes(data),
            detail=1,
            paragraph=self._settings.paragraph,
        )
        texts: list[str] = []
        confidences: list[float] = []
        for item in results:
            if len(item) < 3:
                continue
            text = str(item[1]).strip()
            if not text:
                continue
            texts.append(text)
            try:
                confidences.append(float(item[2]))
            except (TypeError, ValueError):
                continue
        confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
        return EngineOcrResult(text="\n".join(texts).strip(), confidence=confidence)


class RapidOcrEngine(BaseImageEngine):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        from rapidocr_onnxruntime import RapidOCR

        if settings.ocr_device not in {"cpu", "auto"}:
            log.warning("RapidOCR currently uses CPU in this service; requested OCR_DEVICE=%s", settings.ocr_device)
        self._engine = RapidOCR()
        self.device_name = "cpu"

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        result, _elapsed = self._engine(self._image_from_bytes(data))
        lines: list[str] = []
        confidences: list[float] = []
        for item in result or []:
            if len(item) < 3:
                continue
            text = str(item[1]).strip()
            if not text:
                continue
            lines.append(text)
            try:
                confidences.append(float(item[2]))
            except (TypeError, ValueError):
                continue
        confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
        return EngineOcrResult(text="\n".join(lines).strip(), confidence=confidence)


class TesseractOcrEngine(BaseImageEngine):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        import pytesseract

        self._pytesseract = pytesseract
        if settings.tesseract_cmd:
            self._pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        self._lang = _to_tesseract_languages(settings.ocr_languages)
        self.device_name = "cpu"

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        output_type = self._pytesseract.Output.DICT
        image = Image.open(io.BytesIO(data)).convert("RGB")
        warnings: list[str] = []
        try:
            data_dict = self._pytesseract.image_to_data(image, lang=self._lang, output_type=output_type)
        except self._pytesseract.TesseractError as exc:
            fallback_lang = "eng" if "eng" in self._lang.split("+") and self._lang != "eng" else None
            if fallback_lang is None:
                return EngineOcrResult(text="", warnings=[str(exc)])
            warnings.append(f"requested lang={self._lang} unavailable, retried with {fallback_lang}")
            data_dict = self._pytesseract.image_to_data(image, lang=fallback_lang, output_type=output_type)
        parts: list[str] = []
        confidences: list[float] = []
        for text, conf in zip(data_dict.get("text", []), data_dict.get("conf", []), strict=False):
            normalized = str(text or "").strip()
            if not normalized:
                continue
            parts.append(normalized)
            try:
                score = float(conf)
            except (TypeError, ValueError):
                continue
            if score >= 0:
                confidences.append(score / 100.0)
        if not parts:
            warnings.append(f"no text recognized with tesseract lang={self._lang}")
        confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
        return EngineOcrResult(text=" ".join(parts).strip(), confidence=confidence, warnings=warnings)


def _to_tesseract_languages(values: tuple[str, ...]) -> str:
    mapping = {
        "en": "eng",
        "eng": "eng",
        "ch_sim": "chi_sim",
        "chi_sim": "chi_sim",
    }
    resolved = [mapping.get(value.strip().lower(), value.strip()) for value in values if value.strip()]
    return "+".join(resolved or ["eng"])
