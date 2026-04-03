# Remote OCR Provider Benchmark

- Generated at: 2026-04-03T04:23:28.072183+00:00
- Host: Dereks-MacBook-Air-13.local
- Python: 3.12.11
- Method: harder synthetic challenge set with low contrast, rotation, and table-like screenshots; image cases are tested directly, PDF/DOCX/PPTX cases embed multiple challenge images and run through the normal document markdown ingest path.

## Engine Summary

| Engine | Kind | Avg Score | Avg Elapsed (ms) |
| --- | --- | ---: | ---: |
| easyocr-direct-local | direct | 0.0000 | 2070.70 |
| paddleocr-server-remote-cpu | http | 0.9994 | 619.66 |
| rapidocr-direct-local | direct | 0.9994 | 1278.05 |
| tesseract-direct-local | direct | 0.5635 | 200.13 |

## Per Fixture

| Engine | Fixture | Status | Score | Elapsed (ms) | Warnings |
| --- | --- | --- | ---: | ---: | --- |
| rapidocr-direct-local | image-clean | succeeded | 1.0000 | 672.17 |  |
| rapidocr-direct-local | image-low-contrast | succeeded | 1.0000 | 704.35 |  |
| rapidocr-direct-local | image-rotated | succeeded | 1.0000 | 503.94 |  |
| rapidocr-direct-local | image-table | succeeded | 1.0000 | 611.06 |  |
| rapidocr-direct-local | pdf-challenge | succeeded | 1.0000 | 2485.72 |  |
| rapidocr-direct-local | docx-challenge | succeeded | 1.0000 | 2057.72 |  |
| rapidocr-direct-local | pptx-challenge | succeeded | 0.9956 | 1911.41 |  |
| tesseract-direct-local | image-clean | succeeded | 0.7119 | 77.87 |  |
| tesseract-direct-local | image-low-contrast | succeeded | 0.7164 | 80.68 |  |
| tesseract-direct-local | image-rotated | succeeded | 0.3860 | 88.87 |  |
| tesseract-direct-local | image-table | succeeded | 0.3902 | 80.52 |  |
| tesseract-direct-local | pdf-challenge | succeeded | 0.6000 | 399.74 |  |
| tesseract-direct-local | docx-challenge | succeeded | 0.5714 | 335.43 |  |
| tesseract-direct-local | pptx-challenge | succeeded | 0.5689 | 337.80 |  |
| easyocr-direct-local | image-clean | failed | 0.0000 | 549.09 | DocumentConversionError: OCR produced no usable text for challenge-clean.png |
| easyocr-direct-local | image-low-contrast | failed | 0.0000 | 571.53 | DocumentConversionError: OCR produced no usable text for challenge-low-contrast.png |
| easyocr-direct-local | image-rotated | failed | 0.0000 | 776.35 | DocumentConversionError: OCR produced no usable text for challenge-rotated.png |
| easyocr-direct-local | image-table | failed | 0.0000 | 620.11 | DocumentConversionError: OCR produced no usable text for challenge-table.png |
| easyocr-direct-local | pdf-challenge | failed | 0.0000 | 7149.59 | OCR returned no text for page 2; OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 3 |
| easyocr-direct-local | docx-challenge | failed | 0.0000 | 2294.26 | OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 3; OCR returned no text for embedded image 4 |
| easyocr-direct-local | pptx-challenge | failed | 0.0000 | 2533.98 | OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 1; OCR returned no text for embedded image 2 |
| paddleocr-server-remote-cpu | image-clean | succeeded | 1.0000 | 314.01 |  |
| paddleocr-server-remote-cpu | image-low-contrast | succeeded | 1.0000 | 359.52 |  |
| paddleocr-server-remote-cpu | image-rotated | succeeded | 1.0000 | 291.84 |  |
| paddleocr-server-remote-cpu | image-table | succeeded | 1.0000 | 310.21 |  |
| paddleocr-server-remote-cpu | pdf-challenge | succeeded | 1.0000 | 1572.18 |  |
| paddleocr-server-remote-cpu | docx-challenge | succeeded | 1.0000 | 694.25 |  |
| paddleocr-server-remote-cpu | pptx-challenge | succeeded | 0.9956 | 795.61 |  |

## Samples

- `rapidocr-direct-local` on `image-clean`: `城投债 Credit Update / Q12026风险提示45.2%`
- `rapidocr-direct-local` on `image-low-contrast`: `并表口径Revenue1.28bn / 现金回收率93.4%/watchlist`
- `rapidocr-direct-local` on `image-rotated`: `2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y`
- `rapidocr-direct-local` on `image-table`: `项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `rapidocr-direct-local` on `pdf-challenge`: `城投债 Credit Update / Q12026风险提示45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%/watchlist / 2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `rapidocr-direct-local` on `docx-challenge`: `城投债 Credit Update / Q12026风险提示45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%/watchlist / 2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `rapidocr-direct-local` on `pptx-challenge`: `城投债 Credit Update / Q12026风险提示45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%/watchlist /  2 / 2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `tesseract-direct-local` on `image-clean`: `inet Credit Update Q1 2026 Mkitem 45.2%`
- `tesseract-direct-local` on `image-low-contrast`: `F2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o`
- `tesseract-direct-local` on `image-rotated`: `2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE`
- `tesseract-direct-local` on `image-table`: `4.52% 38.6bn AA+ Sue a =| EPR`
- `tesseract-direct-local` on `pdf-challenge`: `inet Credit Update Q1 2026 Mkitem 45.2% / F2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o / 2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE / ES =I 4.52% AA+ 38.6bn`
- `tesseract-direct-local` on `docx-challenge`: `inet Credit Update Q1 2026 Mkitem 45.2% / F2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o / 2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE / 4.52% 38.6bn AA+ Sue a =| EPR`
- `tesseract-direct-local` on `pptx-challenge`: `inet Credit Update Q1 2026 Mkitem 45.2% / F2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o /  2 / 2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE / 4.52% 38.6bn AA+ Sue a =| EPR`
- `easyocr-direct-local` on `image-clean`: ``
- `easyocr-direct-local` on `image-low-contrast`: ``
- `easyocr-direct-local` on `image-rotated`: ``
- `easyocr-direct-local` on `image-table`: ``
- `easyocr-direct-local` on `pdf-challenge`: ``
- `easyocr-direct-local` on `docx-challenge`: ``
- `easyocr-direct-local` on `pptx-challenge`: ``
- `paddleocr-server-remote-cpu` on `image-clean`: `城投债Credit Update / Q1 2026 风险提示 45.2%`
- `paddleocr-server-remote-cpu` on `image-low-contrast`: `并表口径Revenue1.28bn / 现金回收率93.4%/watchlist`
- `paddleocr-server-remote-cpu` on `image-rotated`: `2026Q1到期分布8.2bn / AA+／城投平台/债务久期3.4y`
- `paddleocr-server-remote-cpu` on `image-table`: `项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `paddleocr-server-remote-cpu` on `pdf-challenge`: `城投债Credit Update / Q1 2026 风险提示 45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%/watchlist / 2026Q1到期分布8.2bn / AA+／城投平台/债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `paddleocr-server-remote-cpu` on `docx-challenge`: `城投债Credit Update / Q1 2026 风险提示 45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%/watchlist / 2026Q1到期分布8.2bn / AA+／城投平台/债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `paddleocr-server-remote-cpu` on `pptx-challenge`: `城投债Credit Update / Q1 2026 风险提示 45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%/watchlist /  2 / 2026Q1到期分布8.2bn / AA+／城投平台/债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`

## Raw JSON

```json
{
  "environment": {
    "generated_at": "2026-04-03T04:23:28.072183+00:00",
    "host": "Dereks-MacBook-Air-13.local",
    "python": "3.12.11"
  },
  "rows": [
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "image-clean",
      "ocr_status": "succeeded",
      "elapsed_ms": 672.17,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%",
      "warnings": []
    },
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "image-low-contrast",
      "ocr_status": "succeeded",
      "elapsed_ms": 704.35,
      "score": 1.0,
      "ocr_text": "并表口径Revenue1.28bn\n现金回收率93.4%/watchlist",
      "warnings": []
    },
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "image-rotated",
      "ocr_status": "succeeded",
      "elapsed_ms": 503.94,
      "score": 1.0,
      "ocr_text": "2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y",
      "warnings": []
    },
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "image-table",
      "ocr_status": "succeeded",
      "elapsed_ms": 611.06,
      "score": 1.0,
      "ocr_text": "项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "pdf-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 2485.72,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%/watchlist\n2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "docx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 2057.72,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%/watchlist\n2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "rapidocr-direct-local",
      "kind": "direct",
      "fixture": "pptx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 1911.41,
      "score": 0.9956,
      "ocr_text": "城投债 Credit Update\nQ12026风险提示45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%/watchlist\n 2\n2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "image-clean",
      "ocr_status": "succeeded",
      "elapsed_ms": 77.87,
      "score": 0.7119,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "image-low-contrast",
      "ocr_status": "succeeded",
      "elapsed_ms": 80.68,
      "score": 0.7164,
      "ocr_text": "F2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "image-rotated",
      "ocr_status": "succeeded",
      "elapsed_ms": 88.87,
      "score": 0.386,
      "ocr_text": "2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "image-table",
      "ocr_status": "succeeded",
      "elapsed_ms": 80.52,
      "score": 0.3902,
      "ocr_text": "4.52% 38.6bn AA+ Sue a =| EPR",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "pdf-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 399.74,
      "score": 0.6,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%\nF2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o\n2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE\nES =I 4.52% AA+ 38.6bn",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "docx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 335.43,
      "score": 0.5714,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%\nF2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o\n2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE\n4.52% 38.6bn AA+ Sue a =| EPR",
      "warnings": []
    },
    {
      "engine": "tesseract-direct-local",
      "kind": "direct",
      "fixture": "pptx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 337.8,
      "score": 0.5689,
      "ocr_text": "inet Credit Update Q1 2026 Mkitem 45.2%\nF2z11{% Revenue 1.28bn IBEW 93.4% / watchlist o\n 2\n2026Q1 BRAG E g.20n EB / mene 3.Ay Ade | BEE\n4.52% 38.6bn AA+ Sue a =| EPR",
      "warnings": []
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "image-clean",
      "ocr_status": "failed",
      "elapsed_ms": 549.09,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-clean.png"
      ]
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "image-low-contrast",
      "ocr_status": "failed",
      "elapsed_ms": 571.53,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-low-contrast.png"
      ]
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "image-rotated",
      "ocr_status": "failed",
      "elapsed_ms": 776.35,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-rotated.png"
      ]
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "image-table",
      "ocr_status": "failed",
      "elapsed_ms": 620.11,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-table.png"
      ]
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "pdf-challenge",
      "ocr_status": "failed",
      "elapsed_ms": 7149.59,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for page 2",
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2",
        "OCR returned no text for embedded image 3"
      ]
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "docx-challenge",
      "ocr_status": "failed",
      "elapsed_ms": 2294.26,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2",
        "OCR returned no text for embedded image 3",
        "OCR returned no text for embedded image 4"
      ]
    },
    {
      "engine": "easyocr-direct-local",
      "kind": "direct",
      "fixture": "pptx-challenge",
      "ocr_status": "failed",
      "elapsed_ms": 2533.98,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2",
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2"
      ]
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "image-clean",
      "ocr_status": "succeeded",
      "elapsed_ms": 314.01,
      "score": 1.0,
      "ocr_text": "城投债Credit Update\nQ1 2026 风险提示 45.2%",
      "warnings": []
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "image-low-contrast",
      "ocr_status": "succeeded",
      "elapsed_ms": 359.52,
      "score": 1.0,
      "ocr_text": "并表口径Revenue1.28bn\n现金回收率93.4%/watchlist",
      "warnings": []
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "image-rotated",
      "ocr_status": "succeeded",
      "elapsed_ms": 291.84,
      "score": 1.0,
      "ocr_text": "2026Q1到期分布8.2bn\nAA+／城投平台/债务久期3.4y",
      "warnings": []
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "image-table",
      "ocr_status": "succeeded",
      "elapsed_ms": 310.21,
      "score": 1.0,
      "ocr_text": "项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "pdf-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 1572.18,
      "score": 1.0,
      "ocr_text": "城投债Credit Update\nQ1 2026 风险提示 45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%/watchlist\n2026Q1到期分布8.2bn\nAA+／城投平台/债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "docx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 694.25,
      "score": 1.0,
      "ocr_text": "城投债Credit Update\nQ1 2026 风险提示 45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%/watchlist\n2026Q1到期分布8.2bn\nAA+／城投平台/债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "paddleocr-server-remote-cpu",
      "kind": "http",
      "fixture": "pptx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 795.61,
      "score": 0.9956,
      "ocr_text": "城投债Credit Update\nQ1 2026 风险提示 45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%/watchlist\n 2\n2026Q1到期分布8.2bn\nAA+／城投平台/债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    }
  ]
}
```
