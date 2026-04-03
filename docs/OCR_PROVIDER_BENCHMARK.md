# Document OCR Benchmark

- Generated at: 2026-04-03T03:45:01.555096+00:00
- Host: Dereks-MacBook-Air-13.local
- Python: 3.12.11
- ONNX Runtime providers: CoreMLExecutionProvider, AzureExecutionProvider, CPUExecutionProvider
- Torch MPS built/available: True/True
- Method: generated image text is embedded into image / PDF / DOCX / PPTX; score compares OCR-only extracted text against the expected image text.

## Findings

- On this macOS host, `rapidocr-macos-coreml` matched `rapidocr-local-cpu` accuracy but was materially slower, so CPU remains the better local default.
- PyTorch MPS was available and `easyocr-macos-mps` executed on Metal, but it still produced no usable text on these fixtures.
- Tesseract remained the fastest local option, but its mixed Chinese+English accuracy stayed materially below RapidOCR in this benchmark.

| Engine | Fixture | Status | Score | Elapsed (ms) | Warnings |
| --- | --- | --- | ---: | ---: | --- |
| rapidocr-local-cpu | image | succeeded | 1.0000 | 453.30 |  |
| rapidocr-local-cpu | pdf | succeeded | 1.0000 | 452.02 |  |
| rapidocr-local-cpu | docx | succeeded | 1.0000 | 519.60 |  |
| rapidocr-local-cpu | pptx | succeeded | 1.0000 | 384.52 |  |
| tesseract-local-cpu | image | succeeded | 0.7119 | 75.64 |  |
| tesseract-local-cpu | pdf | succeeded | 0.7119 | 80.58 |  |
| tesseract-local-cpu | docx | succeeded | 0.7119 | 78.57 |  |
| tesseract-local-cpu | pptx | succeeded | 0.7119 | 79.83 |  |
| easyocr-local-cpu | image | failed | 0.0000 | 506.94 | DocumentConversionError: OCR produced no usable text for benchmark-image.png |
| easyocr-local-cpu | pdf | failed | 0.0000 | 460.22 | OCR returned no text for embedded image 1 |
| easyocr-local-cpu | docx | failed | 0.0000 | 2676.46 | OCR returned no text for embedded image 1 |
| easyocr-local-cpu | pptx | failed | 0.0000 | 1290.65 | OCR returned no text for embedded image 1 |
| rapidocr-macos-coreml | image | succeeded | 1.0000 | 1654.55 |  |
| rapidocr-macos-coreml | pdf | succeeded | 1.0000 | 1593.66 |  |
| rapidocr-macos-coreml | docx | succeeded | 1.0000 | 1625.56 |  |
| rapidocr-macos-coreml | pptx | succeeded | 1.0000 | 1650.75 |  |
| easyocr-macos-mps | image | failed | 0.0000 | 121.40 | DocumentConversionError: OCR produced no usable text for benchmark-image.png |
| easyocr-macos-mps | pdf | failed | 0.0000 | 127.85 | OCR returned no text for embedded image 1 |
| easyocr-macos-mps | docx | failed | 0.0000 | 125.05 | OCR returned no text for embedded image 1 |
| easyocr-macos-mps | pptx | failed | 0.0000 | 126.95 | OCR returned no text for embedded image 1 |

## Samples

- `rapidocr-local-cpu` on `image`: `城投债 Credit Update / Q12026风险提示45.2%`
- `rapidocr-local-cpu` on `pdf`: `城投债 Credit Update / Q12026风险提示45.2%`
- `rapidocr-local-cpu` on `docx`: `城投债 Credit Update / Q12026风险提示45.2%`
- `rapidocr-local-cpu` on `pptx`: `城投债 Credit Update / Q12026风险提示45.2%`
- `tesseract-local-cpu` on `image`: `inet Credit Update Q1 2026 Mkitem 45.2%`
- `tesseract-local-cpu` on `pdf`: `inet Credit Update Q1 2026 Mkitem 45.2%`
- `tesseract-local-cpu` on `docx`: `inet Credit Update Q1 2026 Mkitem 45.2%`
- `tesseract-local-cpu` on `pptx`: `inet Credit Update Q1 2026 Mkitem 45.2%`
- `easyocr-local-cpu` on `image`: ``
- `easyocr-local-cpu` on `pdf`: ``
- `easyocr-local-cpu` on `docx`: ``
- `easyocr-local-cpu` on `pptx`: ``
- `rapidocr-macos-coreml` on `image`: `城投债 Credit Update / Q1 2026 风险提示 45.2%`
- `rapidocr-macos-coreml` on `pdf`: `城投债 Credit Update / Q1 2026 风险提示 45.2%`
- `rapidocr-macos-coreml` on `docx`: `城投债 Credit Update / Q1 2026 风险提示 45.2%`
- `rapidocr-macos-coreml` on `pptx`: `城投债 Credit Update / Q1 2026 风险提示 45.2%`
- `easyocr-macos-mps` on `image`: ``
- `easyocr-macos-mps` on `pdf`: ``
- `easyocr-macos-mps` on `docx`: ``
- `easyocr-macos-mps` on `pptx`: ``

## Raw JSON

```json
{
  "environment": {
    "generated_at": "2026-04-03T03:45:01.555096+00:00",
    "host": "Dereks-MacBook-Air-13.local",
    "python": "3.12.11",
    "onnxruntime_providers": [
      "CoreMLExecutionProvider",
      "AzureExecutionProvider",
      "CPUExecutionProvider"
    ],
    "torch_mps_built": true,
    "torch_mps_available": true
  },
  "rows": [
    {
      "fixture": "image",
      "ocr_status": "succeeded",
      "elapsed_ms": 453.3,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%",
      "warnings": [],
      "engine": "rapidocr-local-cpu"
    },
    {
      "fixture": "pdf",
      "ocr_status": "succeeded",
      "elapsed_ms": 452.02,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%",
      "warnings": [],
      "engine": "rapidocr-local-cpu"
    },
    {
      "fixture": "docx",
      "ocr_status": "succeeded",
      "elapsed_ms": 519.6,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%",
      "warnings": [],
      "engine": "rapidocr-local-cpu"
    },
    {
      "fixture": "pptx",
      "ocr_status": "succeeded",
      "elapsed_ms": 384.52,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%",
      "warnings": [],
      "engine": "rapidocr-local-cpu"
    },
    {
      "fixture": "image",
      "ocr_status": "succeeded",
      "elapsed_ms": 75.64,
      "score": 0.7119,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%",
      "warnings": [],
      "engine": "tesseract-local-cpu"
    },
    {
      "fixture": "pdf",
      "ocr_status": "succeeded",
      "elapsed_ms": 80.58,
      "score": 0.7119,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%",
      "warnings": [],
      "engine": "tesseract-local-cpu"
    },
    {
      "fixture": "docx",
      "ocr_status": "succeeded",
      "elapsed_ms": 78.57,
      "score": 0.7119,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%",
      "warnings": [],
      "engine": "tesseract-local-cpu"
    },
    {
      "fixture": "pptx",
      "ocr_status": "succeeded",
      "elapsed_ms": 79.83,
      "score": 0.7119,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%",
      "warnings": [],
      "engine": "tesseract-local-cpu"
    },
    {
      "fixture": "image",
      "ocr_status": "failed",
      "elapsed_ms": 506.94,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for benchmark-image.png"
      ],
      "engine": "easyocr-local-cpu"
    },
    {
      "fixture": "pdf",
      "ocr_status": "failed",
      "elapsed_ms": 460.22,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1"
      ],
      "engine": "easyocr-local-cpu"
    },
    {
      "fixture": "docx",
      "ocr_status": "failed",
      "elapsed_ms": 2676.46,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1"
      ],
      "engine": "easyocr-local-cpu"
    },
    {
      "fixture": "pptx",
      "ocr_status": "failed",
      "elapsed_ms": 1290.65,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1"
      ],
      "engine": "easyocr-local-cpu"
    },
    {
      "fixture": "image",
      "ocr_status": "succeeded",
      "elapsed_ms": 1654.55,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%",
      "warnings": [],
      "engine": "rapidocr-macos-coreml"
    },
    {
      "fixture": "pdf",
      "ocr_status": "succeeded",
      "elapsed_ms": 1593.66,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%",
      "warnings": [],
      "engine": "rapidocr-macos-coreml"
    },
    {
      "fixture": "docx",
      "ocr_status": "succeeded",
      "elapsed_ms": 1625.56,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%",
      "warnings": [],
      "engine": "rapidocr-macos-coreml"
    },
    {
      "fixture": "pptx",
      "ocr_status": "succeeded",
      "elapsed_ms": 1650.75,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%",
      "warnings": [],
      "engine": "rapidocr-macos-coreml"
    },
    {
      "fixture": "image",
      "ocr_status": "failed",
      "elapsed_ms": 121.4,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for benchmark-image.png"
      ],
      "engine": "easyocr-macos-mps"
    },
    {
      "fixture": "pdf",
      "ocr_status": "failed",
      "elapsed_ms": 127.85,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1"
      ],
      "engine": "easyocr-macos-mps"
    },
    {
      "fixture": "docx",
      "ocr_status": "failed",
      "elapsed_ms": 125.05,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1"
      ],
      "engine": "easyocr-macos-mps"
    },
    {
      "fixture": "pptx",
      "ocr_status": "failed",
      "elapsed_ms": 126.95,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1"
      ],
      "engine": "easyocr-macos-mps"
    }
  ]
}
```
