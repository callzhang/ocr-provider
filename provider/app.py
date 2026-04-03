from __future__ import annotations

import base64
import io
import logging
from typing import Any, Literal

import fitz
import numpy as np
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from PIL import Image

from provider.config import Settings

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
        self._reader = self._load_reader()

    def _load_reader(self) -> Any:
        import torch
        import easyocr

        self._settings.model_storage_dir.mkdir(parents=True, exist_ok=True)
        use_gpu = self._settings.use_gpu and torch.cuda.is_available()
        reader = easyocr.Reader(
            list(self._settings.ocr_languages),
            gpu=use_gpu,
            model_storage_directory=str(self._settings.model_storage_dir),
            download_enabled=True,
        )
        self.device_name = "cuda" if use_gpu else "cpu"
        return reader

    def _image_from_bytes(self, data: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        return np.asarray(image)

    def _read_lines(self, image: np.ndarray) -> tuple[str, float | None]:
        results = self._reader.readtext(image, detail=1, paragraph=self._settings.paragraph)
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
        return "\n".join(texts).strip(), confidence

    def ocr_image(self, data: bytes) -> tuple[str, float | None]:
        return self._read_lines(self._image_from_bytes(data))

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
            text, confidence = self.ocr_image(pixmap.tobytes("png"))
            page_results.append(
                OcrPageResult(
                    page_number=page_number,
                    text=text,
                    confidence=confidence,
                    warnings=[] if text else [f"no text recognized on page {page_number}"],
                )
            )
        return page_results


def _require_api_key(settings: Settings, authorization: str | None) -> None:
    if not settings.api_key:
        return
    expected = f"Bearer {settings.api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


def create_app(settings: Settings | None = None, runtime: OcrRuntime | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_runtime = runtime or OcrRuntime(resolved_settings)
    app = FastAPI(title="OCR Provider", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "service": resolved_settings.service_name,
            "model": resolved_settings.model_id,
            "languages": list(resolved_settings.ocr_languages),
            "device": resolved_runtime.device_name,
        }

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
            text, confidence = resolved_runtime.ocr_image(data)
            warnings = [] if text else ["no text recognized"]
            items.append(
                OcrItem(
                    source_id=item.source_id,
                    text=text,
                    confidence=confidence,
                    warnings=warnings,
                )
            )

        return OcrResponse(model=req.model or resolved_settings.model_id, data=items)

    return app


app = create_app()
