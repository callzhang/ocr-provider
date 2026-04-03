from __future__ import annotations

import base64
from contextlib import contextmanager
import logging
import os
import subprocess
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
        self._engine: OcrEngine = build_engine(settings)
        self.device_name = self._engine.device_name
        self._admission = RuntimeAdmissionController(settings, self.device_name)

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
            yield

    def admission_status(self) -> dict[str, Any]:
        return self._admission.status()


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
