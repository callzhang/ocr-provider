# OCR Provider

Standalone OCR service for `memory-connector` document ingest.

## Purpose

- Run independently from `memory-connector`
- Keep OCR execution isolated from embedding traffic even on the same GPU host
- Expose one HTTP API for image uploads and scanned-PDF fallback
- Deploy on `stardust-gpu4` and publish through Cloudflare under `preseen.ai`

## API

- `GET /healthz`
- `GET /v1/models`
- `POST /v1/ocr`

`/v1/ocr` accepts base64-encoded image or PDF payloads:

```json
{
  "model": "easyocr:ch_sim+en",
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

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
cp .env.example .env
set -a && source .env && set +a
uvicorn provider.app:app --host 127.0.0.1 --port 7998
```

## Stardust GPU4

- Repo target: `stardust@stardust-gpu4:~/Projects/ocr-provider`
- Private bind: `127.0.0.1:7998`
- Public base URL: `https://ocr.preseen.ai/v1`

Recommended host workflow:

```bash
bash scripts/deploy_gpu4.sh
ssh stardust-gpu4-stardust
cd ~/Projects/ocr-provider
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
