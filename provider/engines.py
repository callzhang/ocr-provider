from __future__ import annotations

import io
import logging
import os
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass, field
from dataclasses import replace
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


def build_engine(settings: Settings, ocr_device_override: str | None = None) -> OcrEngine:
    if ocr_device_override is not None:
        settings = replace(settings, ocr_device=ocr_device_override)
    provider = settings.ocr_provider.strip().lower()
    if provider == "easyocr":
        return EasyOcrEngine(settings)
    if provider == "onnxtr":
        return OnnxtrOcrEngine(settings)
    if provider == "paddleocr":
        return PaddleOcrEngine(settings)
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
        wants_cuda = settings.ocr_device == "cuda" or (settings.ocr_device == "auto" and torch.cuda.is_available())
        wants_mps = settings.ocr_device in {"mps", "coreml"} or (
            settings.ocr_device == "auto" and _torch_mps_available(torch)
        )
        if settings.ocr_device == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("OCR_DEVICE=mps requested for easyocr, but torch.backends.mps.is_available() is false")
        if settings.ocr_device == "coreml" and not _torch_mps_available(torch):
            raise RuntimeError("OCR_DEVICE=coreml requested for easyocr, but torch.backends.mps.is_available() is false")
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


class OnnxtrOcrEngine(BaseImageEngine):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        from onnxtr.models import EngineConfig, ocr_predictor

        settings.model_storage_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("ONNXTR_CACHE_DIR", str(settings.model_storage_dir))
        providers, device_name = _resolve_onnx_execution_providers(settings.ocr_device)
        self._predictor = ocr_predictor(
            det_engine_cfg=EngineConfig(providers=providers),
            reco_engine_cfg=EngineConfig(providers=providers),
            clf_engine_cfg=EngineConfig(providers=providers),
        )
        self.device_name = device_name

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        from onnxtr.io import DocumentFile

        document = DocumentFile.from_images(data)
        result = self._predictor(document)
        text = result.render().strip()
        confidences = _collect_onnxtr_confidences(result)
        warnings = [] if text else ["onnxtr returned no text"]
        return EngineOcrResult(
            text=text,
            confidence=round(sum(confidences) / len(confidences), 4) if confidences else None,
            warnings=warnings,
        )


class RapidOcrEngine(BaseImageEngine):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        from rapidocr_onnxruntime import RapidOCR
        from rapidocr_onnxruntime.utils.infer_engine import OrtInferSession as BaseOrtInferSession
        import rapidocr_onnxruntime.ch_ppocr_cls.text_cls as text_cls
        import rapidocr_onnxruntime.ch_ppocr_det.text_detect as text_detect
        import rapidocr_onnxruntime.ch_ppocr_rec.text_recognize as text_recognize
        import rapidocr_onnxruntime.utils as rapid_utils

        available_providers = _available_onnx_providers()
        wants_cuda = settings.ocr_device == "cuda" or (
            settings.ocr_device == "auto" and "CUDAExecutionProvider" in available_providers
        )
        wants_coreml = settings.ocr_device in {"coreml", "mps"} or (
            settings.ocr_device == "auto"
            and not wants_cuda
            and "CoreMLExecutionProvider" in available_providers
        )
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

        if wants_cuda:
            self._engine = RapidOCR(det_use_cuda=True, cls_use_cuda=True, rec_use_cuda=True)
            providers = self._engine.text_det.infer.session.get_providers()
            self.device_name = "cuda" if providers and providers[0] == "CUDAExecutionProvider" else "cpu"
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


class PaddleOcrEngine(BaseImageEngine):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._cache_dir = settings.model_storage_dir / "paddlex-cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        if settings.paddle_disable_model_source_check:
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
        os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "huggingface")
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(self._cache_dir))
        _install_modelscope_stub()

        from paddleocr import PaddleOCR

        det_model, rec_model = _resolve_paddle_model_names(settings)
        device = _resolve_paddle_device(settings.ocr_device)
        lang = settings.paddle_lang or _resolve_paddle_lang(settings.ocr_languages)
        kwargs = {
            "device": device,
            "text_detection_model_name": det_model,
            "text_recognition_model_name": rec_model,
            "use_doc_orientation_classify": settings.paddle_use_doc_orientation_classify,
            "use_doc_unwarping": settings.paddle_use_doc_unwarping,
            "use_textline_orientation": settings.paddle_use_textline_orientation,
        }
        if not (det_model and rec_model):
            kwargs["lang"] = lang
        self._ocr = PaddleOCR(**kwargs)
        self.provider_name = "paddleocr"
        self.model_id = f"paddleocr:{det_model}+{rec_model}"
        self.device_name = device

    def ocr_image(self, data: bytes) -> EngineOcrResult:
        result_list = list(self._ocr.predict(self._image_from_bytes(data)))
        if not result_list:
            return EngineOcrResult(text="", warnings=["paddleocr returned no result rows"])
        result = result_list[0]
        texts = [str(item).strip() for item in result.get("rec_texts", []) if str(item).strip()]
        scores = []
        for item in result.get("rec_scores", []):
            try:
                scores.append(float(item))
            except (TypeError, ValueError):
                continue
        warnings: list[str] = []
        if not texts:
            warnings.append("paddleocr returned no text lines")
        confidence = round(sum(scores) / len(scores), 4) if scores else None
        return EngineOcrResult(text="\n".join(texts).strip(), confidence=confidence, warnings=warnings)


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


def _available_onnx_providers() -> list[str]:
    try:
        import onnxruntime as ort
    except ModuleNotFoundError:
        return []
    return list(ort.get_available_providers())


def _resolve_onnx_execution_providers(requested_device: str) -> tuple[list[tuple[str, dict[str, object]]], str]:
    normalized = str(requested_device or "cpu").strip().lower()
    available = _available_onnx_providers()
    cpu = ("CPUExecutionProvider", {"arena_extend_strategy": "kSameAsRequested"})
    if normalized == "auto":
        if "CUDAExecutionProvider" in available:
            normalized = "cuda"
        elif "CoreMLExecutionProvider" in available:
            normalized = "coreml"
        else:
            normalized = "cpu"
    if normalized == "cuda":
        if "CUDAExecutionProvider" in available:
            cuda = (
                "CUDAExecutionProvider",
                {
                    "device_id": 0,
                    "arena_extend_strategy": "kNextPowerOfTwo",
                    "cudnn_conv_algo_search": "DEFAULT",
                    "do_copy_in_default_stream": True,
                },
            )
            return [cuda, cpu], "cuda"
        log.warning("CUDAExecutionProvider unavailable for ONNX-based OCR; falling back to CPU")
    if normalized in {"mps", "coreml"}:
        if "CoreMLExecutionProvider" in available:
            return [("CoreMLExecutionProvider", {}), cpu], "coreml"
        log.warning("CoreMLExecutionProvider unavailable for ONNX-based OCR; falling back to CPU")
    return [cpu], "cpu"


def _torch_mps_available(torch_module: object) -> bool:
    backends = getattr(torch_module, "backends", None)
    mps = getattr(backends, "mps", None)
    is_available = getattr(mps, "is_available", None)
    return bool(is_available and is_available())


def _collect_onnxtr_confidences(element: object) -> list[float]:
    confidences: list[float] = []
    if hasattr(element, "pages"):
        for page in getattr(element, "pages", []):
            confidences.extend(_collect_onnxtr_confidences(page))
        return confidences
    if hasattr(element, "blocks"):
        for block in getattr(element, "blocks", []):
            confidences.extend(_collect_onnxtr_confidences(block))
        return confidences
    if hasattr(element, "lines"):
        for line in getattr(element, "lines", []):
            confidences.extend(_collect_onnxtr_confidences(line))
        return confidences
    if hasattr(element, "words"):
        for word in getattr(element, "words", []):
            value = getattr(word, "confidence", None)
            if value is None:
                continue
            try:
                confidences.append(float(value))
            except (TypeError, ValueError):
                continue
    return confidences


def _to_tesseract_languages(values: tuple[str, ...]) -> str:
    mapping = {
        "en": "eng",
        "eng": "eng",
        "ch_sim": "chi_sim",
        "chi_sim": "chi_sim",
    }
    resolved = [mapping.get(value.strip().lower(), value.strip()) for value in values if value.strip()]
    return "+".join(resolved or ["eng"])


def _resolve_paddle_model_names(settings: Settings) -> tuple[str, str]:
    det = settings.paddle_text_detection_model_name
    rec = settings.paddle_text_recognition_model_name
    if det and rec:
        return det, rec
    model_hint = settings.model_id.lower()
    tier = "server" if "server" in model_hint or settings.ocr_device == "cuda" else "mobile"
    return (
        det or f"PP-OCRv5_{tier}_det",
        rec or f"PP-OCRv5_{tier}_rec",
    )


def _resolve_paddle_lang(values: tuple[str, ...]) -> str:
    normalized = {value.strip().lower() for value in values}
    if any(value in normalized for value in {"ch_sim", "chi_sim", "zh", "ch"}):
        return "ch"
    if normalized == {"en"} or normalized == {"eng"}:
        return "en"
    return "ch"


def _resolve_paddle_device(value: str) -> str:
    normalized = str(value or "cpu").strip().lower()
    if normalized == "cuda":
        return "gpu:0"
    if normalized in {"cpu", "auto"}:
        return "cpu"
    return normalized


def _install_modelscope_stub() -> None:
    if "modelscope" in sys.modules:
        return
    stub = types.ModuleType("modelscope")

    def _snapshot_download(*args, **kwargs):
        raise RuntimeError(
            "modelscope downloads are disabled in this service; use PADDLE_PDX_MODEL_SOURCE=huggingface"
        )

    stub.snapshot_download = _snapshot_download
    sys.modules["modelscope"] = stub


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
