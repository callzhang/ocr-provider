from __future__ import annotations

import io
import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
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
        wants_cuda = settings.ocr_device == "cuda" or (
            settings.ocr_device == "auto" and torch.cuda.is_available()
        )
        wants_mps = settings.ocr_device == "mps" or (
            settings.ocr_device == "auto" and torch.backends.mps.is_available()
        )
        if settings.ocr_device == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("OCR_DEVICE=mps requested for easyocr, but torch.backends.mps.is_available() is false")
        gpu_arg: bool | str = wants_cuda or wants_mps
        if wants_mps:
            gpu_arg = "mps"
        self._reader = easyocr.Reader(
            list(settings.ocr_languages),
            gpu=gpu_arg,
            model_storage_directory=str(settings.model_storage_dir),
            user_network_directory=str(settings.model_storage_dir / "user_network"),
            download_enabled=True,
        )
        if wants_cuda:
            self.device_name = "cuda"
        elif wants_mps:
            self.device_name = "mps"
        else:
            self.device_name = "cpu"

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
        from rapidocr_onnxruntime.utils.infer_engine import OrtInferSession as BaseOrtInferSession
        import rapidocr_onnxruntime.ch_ppocr_cls.text_cls as text_cls
        import rapidocr_onnxruntime.ch_ppocr_det.text_detect as text_detect
        import rapidocr_onnxruntime.ch_ppocr_rec.text_recognize as text_recognize
        import rapidocr_onnxruntime.utils as rapid_utils

        wants_coreml = settings.ocr_device in {"coreml", "mps"}
        if wants_coreml:
            cache_dir = settings.model_storage_dir / "coreml-cache"
            provider_options = {
                "ModelCacheDirectory": str(cache_dir),
                "MLComputeUnits": "CPUAndGPU",
                "RequireStaticInputShapes": "0",
                "EnableOnSubgraphs": "0",
            }

            class AppleOrtInferSession(BaseOrtInferSession):
                def __init__(self, config: dict[str, object]):
                    self.cfg_use_coreml = bool(config.get("use_coreml"))
                    self.cfg_coreml_provider_options = dict(config.get("coreml_provider_options") or {})
                    self.use_cuda = False
                    self.use_directml = False
                    super().__init__(config)

                def _get_ep_list(self) -> list[tuple[str, dict[str, object]]]:
                    if self.cfg_use_coreml:
                        if "CoreMLExecutionProvider" in self.had_providers:
                            cpu = ("CPUExecutionProvider", {"arena_extend_strategy": "kSameAsRequested"})
                            return [("CoreMLExecutionProvider", self.cfg_coreml_provider_options), cpu]
                        log.warning(
                            "CoreMLExecutionProvider is unavailable in onnxruntime providers=%s; falling back to CPU",
                            self.had_providers,
                        )
                    return super()._get_ep_list()

                def _verify_providers(self) -> None:
                    super()._verify_providers()
                    if self.cfg_use_coreml and self.session.get_providers()[0] != "CoreMLExecutionProvider":
                        log.warning(
                            "RapidOCR requested CoreML but session is using %s",
                            self.session.get_providers()[0],
                        )

            rapid_utils.OrtInferSession = AppleOrtInferSession
            text_detect.OrtInferSession = AppleOrtInferSession
            text_cls.OrtInferSession = AppleOrtInferSession
            text_recognize.OrtInferSession = AppleOrtInferSession
            with _temporary_tmpdir(cache_dir):
                self._engine = RapidOCR(
                    det_use_coreml=True,
                    cls_use_coreml=True,
                    rec_use_coreml=True,
                    det_coreml_provider_options=provider_options,
                    cls_coreml_provider_options=provider_options,
                    rec_coreml_provider_options=provider_options,
                )
            providers = self._engine.text_det.infer.session.get_providers()
            self.device_name = "coreml" if providers and providers[0] == "CoreMLExecutionProvider" else "cpu"
            return

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


@contextmanager
def _temporary_tmpdir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    previous = {name: os.environ.get(name) for name in ("TMPDIR", "TMP", "TEMP")}
    try:
        for name in ("TMPDIR", "TMP", "TEMP"):
            os.environ[name] = str(path)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
