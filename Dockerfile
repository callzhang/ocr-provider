FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY provider /app/provider

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .[benchmark]

ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=ocr-provider
ENV OCR_PROVIDER=rapidocr
ENV OCR_MODEL=rapidocr:ch_sim+en
ENV OCR_MODEL_ALIAS=rapidocr-zh-en
ENV OCR_LANGUAGES=ch_sim,en
ENV OCR_DEVICE=auto
ENV OCR_PARAGRAPH=true
ENV OCR_MODEL_STORAGE_DIR=/app/runtime-cache/rapidocr-zh-en
ENV PDF_RENDER_SCALE=2.0
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "provider.app:app", "--host", "0.0.0.0", "--port", "8000"]
