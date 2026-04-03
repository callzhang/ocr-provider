# OCR Provider

Standalone OCR service for `memory-connector` document ingest.

## Purpose

- Run independently from `memory-connector`
- Keep OCR execution isolated from embedding traffic even on the same host
- Expose one HTTP API for image uploads, scanned-PDF fallback, and embedded-image OCR
- Use one production default across macOS and Linux hosts

## Production Profile

The service is currently documented and configured around one OCR profile:

- `OCR_PROVIDER=rapidocr`
- `OCR_MODEL=rapidocr:ch_sim+en`
- `OCR_DEVICE=auto`

`OCR_DEVICE=auto` means:

- prefer `cuda` on Linux GPU hosts when ONNX Runtime exposes CUDA
- otherwise prefer `coreml` on macOS when ONNX Runtime exposes CoreML
- otherwise fall back to `cpu`

Core env vars:

```bash
SERVICE_NAME=ocr-provider
OCR_PROVIDER=rapidocr
OCR_MODEL=rapidocr:ch_sim+en
OCR_MODEL_ALIAS=rapidocr-zh-en
OCR_LANGUAGES=ch_sim,en
OCR_DEVICE=auto
OCR_MODEL_STORAGE_DIR=./runtime-cache/rapidocr-zh-en
OCR_PARAGRAPH=true
PDF_RENDER_SCALE=2.0
API_KEY=change-me
```

Notes:

- `rapidocr` is the only production-supported OCR profile in this repo right now.
- The service code still contains experimental engine paths from evaluation work, but deployment docs intentionally standardize on `rapidocr`.
- `rapidocr` uses ONNX Runtime and can route to CUDA or CoreML when the matching execution provider is available.

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

- `.env.example`: `rapidocr` + `auto`, for local runs beside the backend service
- `deployments/local/rapidocr-cpu.env.example`: `rapidocr` + `cpu`, for deterministic local CPU fallback
- `deployments/gpu4/rapidocr-auto.env.example`: `rapidocr` + `auto`, for the shared `stardust-gpu4` host

## Benchmark

The repo is benchmarked from the main workspace with:

```bash
./ocr-provider/.venv/bin/python scripts/benchmark_document_ocr.py
```

Current decision material:

- [OCR_PROVIDER_REALWORLD_BENCHMARK.md](/Users/derek/Projects/memory-connector/docs/OCR_PROVIDER_REALWORLD_BENCHMARK.md)

Decision summary:

- The real-world benchmark uses `dfcfw-page1.png` and ground truth extracted from the corresponding PDF page.
- `rapidocr` was the only tested lightweight engine that produced usable Chinese output on that sample.
- On this macOS host, `rapidocr` under `OCR_DEVICE=auto` resolved to CoreML and scored `0.6866` on the PNG path.

## Stardust GPU4

- Repo target: `stardust@stardust-gpu4:~/Projects/ocr-provider`
- Private bind: `127.0.0.1:7998`
- Public base URL: `https://ocr.preseen.ai/v1`
- Deployment policy: do not modify shared host CUDA or other system-level GPU components

Recommended host workflow:

```bash
bash scripts/deploy_gpu4.sh
ssh stardust-gpu4-stardust
cd ~/Projects/ocr-provider
cp deployments/gpu4/rapidocr-auto.env.example deployments/gpu4/rapidocr-auto.env
./scripts/start_host_instance.sh deployments/gpu4/rapidocr-auto.env
./scripts/start_public_cloudflared.sh deployments/gpu4/rapidocr-auto.env
```

Before starting the named tunnel, create it and attach DNS from a machine already logged into Cloudflare:

```bash
cloudflared tunnel create ocr-provider-preseen-ai
cloudflared tunnel route dns ocr-provider-preseen-ai ocr.preseen.ai
cloudflared tunnel token ocr-provider-preseen-ai
```

Set the returned token into `deployments/gpu4/rapidocr-auto.env`:

```bash
PUBLIC_TUNNEL_TOKEN=<TOKEN>
```

Health checks:

```bash
curl https://ocr.preseen.ai/healthz
curl -H "Authorization: Bearer <API_KEY>" https://ocr.preseen.ai/v1/models
```
