# OCR Provider

Standalone OCR service for `memory-connector` document ingest.

## Purpose

- Run independently from `memory-connector`
- Keep OCR execution isolated from embedding traffic even on the same host
- Expose one HTTP API for image uploads, scanned-PDF fallback, and embedded-image OCR
- Support both lightweight local engines and GPU-oriented engines from the same repo

## Runtime Model

The service now uses explicit env-driven OCR runtime selection instead of implicit `USE_GPU` toggles.

Core env vars:

```bash
SERVICE_NAME=ocr-provider
OCR_PROVIDER=rapidocr          # rapidocr | tesseract | easyocr
OCR_MODEL=rapidocr:ch_sim+en
OCR_MODEL_ALIAS=rapidocr-zh-en
OCR_LANGUAGES=ch_sim,en
OCR_DEVICE=cpu                # cpu | cuda | mps | coreml | auto
OCR_MODEL_STORAGE_DIR=./runtime-cache/rapidocr-zh-en
OCR_PARAGRAPH=true
PDF_RENDER_SCALE=2.0
API_KEY=change-me
```

Notes:

- `rapidocr` is the current recommended lightweight local default.
- On macOS, `rapidocr` can use `OCR_DEVICE=coreml` to route ONNX Runtime through `CoreMLExecutionProvider`.
- `tesseract` is the fastest local CPU option in our benchmark, but quality depends heavily on installed language packs.
- `easyocr` remains available for CPU/GPU runs and is the current GPU deployment path on `stardust-gpu4`; on macOS it also accepts `OCR_DEVICE=mps` when PyTorch MPS is available.

## API

- `GET /healthz`
- `GET /v1/models`
- `POST /v1/ocr`

`/v1/ocr` accepts base64-encoded image or PDF payloads:

```json
{
  "model": "rapidocr:ch_sim+en",
  "languages": ["ch_sim", "en"],
  "inputs": [
    {
      "source_id": "pdf",
      "mime_type": "application/pdf",
      "data_base64": "<base64>",
      "page_numbers": [1, 3]
    }
  ]
}
```

## Local Development

Recommended local bootstrap:

```bash
cp .env.example .env
set -a && source .env && set +a
./scripts/bootstrap_venv.sh
./scripts/start_host_instance.sh .env
```

Sample local presets:

- `.env.example`: `rapidocr` + CPU, meant for running directly beside the backend service
- `deployments/gpu4/easyocr-zh-en.env.example`: `easyocr` + CUDA, meant for `stardust-gpu4`

If you use `tesseract`, make sure the host has the matching language packs installed. On macOS/Homebrew, the stock install may only include `eng`.

## Benchmark

The repo is benchmarked from the main workspace with:

```bash
./ocr-provider/.venv/bin/python scripts/benchmark_document_ocr.py
```

Latest report:

- [OCR_PROVIDER_BENCHMARK.md](/Users/derek/Projects/memory-connector/docs/OCR_PROVIDER_BENCHMARK.md)

At the time of the current report on Derek's local CPU machine:

- `rapidocr-local-cpu` had the best mixed Chinese+English accuracy across `image/pdf/docx/pptx`
- `rapidocr-macos-coreml` matched CPU accuracy on Derek's macOS host, but it was slower than `rapidocr-local-cpu` in the current run
- `tesseract-local-cpu` was the fastest but materially less accurate on Chinese text with the local tessdata setup
- `easyocr-local-cpu` failed on the generated benchmark image and is better kept as the GPU-oriented option unless retuned
- `easyocr-macos-mps` did execute with MPS available on Derek's machine, but still returned no usable text on the benchmark fixtures

## Stardust GPU4

- Repo target: `stardust@stardust-gpu4:~/Projects/ocr-provider`
- Private bind: `127.0.0.1:7998`
- Public base URL: `https://ocr.preseen.ai/v1`

Recommended host workflow:

```bash
bash scripts/deploy_gpu4.sh
ssh stardust-gpu4-stardust
cd ~/Projects/ocr-provider
cp deployments/gpu4/easyocr-zh-en.env.example deployments/gpu4/easyocr-zh-en.env
./scripts/start_host_instance.sh deployments/gpu4/easyocr-zh-en.env
./scripts/start_public_cloudflared.sh deployments/gpu4/easyocr-zh-en.env
```

Before starting the named tunnel, create it and attach DNS from a machine already logged into Cloudflare:

```bash
cloudflared tunnel create ocr-provider-preseen-ai
cloudflared tunnel route dns ocr-provider-preseen-ai ocr.preseen.ai
cloudflared tunnel token ocr-provider-preseen-ai
```

Set the returned token into `deployments/gpu4/easyocr-zh-en.env`:

```bash
PUBLIC_TUNNEL_TOKEN=<TOKEN>
```

Health checks:

```bash
curl https://ocr.preseen.ai/healthz
curl -H "Authorization: Bearer <API_KEY>" https://ocr.preseen.ai/v1/models
```
