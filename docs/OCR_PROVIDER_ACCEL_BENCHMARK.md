# Accelerated OCR Provider Benchmark

- Generated at: 2026-04-03T05:32:26.556960+00:00
- Host: Dereks-MacBook-Air-13.local
- Python: 3.12.11
- Method: harder synthetic challenge set with low contrast, rotation, table screenshots, and a dense two-column screenshot; image cases are tested directly, PDF/DOCX/PPTX cases embed multiple challenge images and run through the normal document markdown ingest path.

## Engine Summary

| Engine | Kind | Success | Avg Score | Avg Elapsed (ms) |
| --- | --- | ---: | ---: | ---: |
| easyocr-auto-local | direct | 0/8 | 0.0000 | 850.64 |
| onnxtr-auto-local | direct | 8/8 | 0.4830 | 3928.05 |
| rapidocr-auto-local | direct | 8/8 | 0.9181 | 4379.62 |

## Per Fixture

| Engine | Fixture | Status | Score | Elapsed (ms) | Warnings |
| --- | --- | --- | ---: | ---: | --- |
| rapidocr-auto-local | image-clean | succeeded | 1.0000 | 1609.73 |  |
| rapidocr-auto-local | image-low-contrast | succeeded | 1.0000 | 2093.62 |  |
| rapidocr-auto-local | image-rotated | succeeded | 1.0000 | 1540.64 |  |
| rapidocr-auto-local | image-table | succeeded | 1.0000 | 2021.23 |  |
| rapidocr-auto-local | image-dense-columns | succeeded | 0.7459 | 1328.02 |  |
| rapidocr-auto-local | pdf-challenge | succeeded | 0.8675 | 8866.22 |  |
| rapidocr-auto-local | docx-challenge | succeeded | 0.8675 | 9242.71 |  |
| rapidocr-auto-local | pptx-challenge | succeeded | 0.8638 | 8334.81 |  |
| easyocr-auto-local | image-clean | failed | 0.0000 | 132.23 | DocumentConversionError: OCR produced no usable text for challenge-clean.png |
| easyocr-auto-local | image-low-contrast | failed | 0.0000 | 685.49 | DocumentConversionError: OCR produced no usable text for challenge-low-contrast.png |
| easyocr-auto-local | image-rotated | failed | 0.0000 | 381.50 | DocumentConversionError: OCR produced no usable text for challenge-rotated.png |
| easyocr-auto-local | image-table | failed | 0.0000 | 177.73 | DocumentConversionError: OCR produced no usable text for challenge-table.png |
| easyocr-auto-local | image-dense-columns | failed | 0.0000 | 1226.87 | DocumentConversionError: OCR produced no usable text for challenge-dense-columns.png |
| easyocr-auto-local | pdf-challenge | failed | 0.0000 | 1780.87 | OCR returned no text for page 2; OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 3 |
| easyocr-auto-local | docx-challenge | failed | 0.0000 | 1211.49 | OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 3; OCR returned no text for embedded image 4; OCR returned no text for embedded image 5 |
| easyocr-auto-local | pptx-challenge | failed | 0.0000 | 1208.98 | OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 1; OCR returned no text for embedded image 2; OCR returned no text for embedded image 1 |
| onnxtr-auto-local | image-clean | succeeded | 0.7000 | 185.08 |  |
| onnxtr-auto-local | image-low-contrast | succeeded | 0.7273 | 208.31 |  |
| onnxtr-auto-local | image-rotated | succeeded | 0.2759 | 881.57 |  |
| onnxtr-auto-local | image-table | succeeded | 0.4255 | 5987.40 |  |
| onnxtr-auto-local | image-dense-columns | succeeded | 0.5514 | 2125.66 |  |
| onnxtr-auto-local | pdf-challenge | succeeded | 0.3715 | 13911.93 |  |
| onnxtr-auto-local | docx-challenge | succeeded | 0.4051 | 2816.67 |  |
| onnxtr-auto-local | pptx-challenge | succeeded | 0.4076 | 5307.78 |  |

## Samples

- `rapidocr-auto-local` on `image-clean`: `城投债 Credit Update / Q1 2026 风险提示 45.2%`
- `rapidocr-auto-local` on `image-low-contrast`: `并表口径Revenue1.28bn / 现金回收率93.4%／watchlist`
- `rapidocr-auto-local` on `image-rotated`: `2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y`
- `rapidocr-auto-local` on `image-table`: `项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn`
- `rapidocr-auto-local` on `image-dense-columns`: `2026年城投平台再融资跟踪 / Left Column / Right Column / 1.净融资-2.3bn / A.债项评级维持AA+ / 2.非标压降17.4% / B.土储去化周期19.6月 / 3.平台现金短债比1.18x / C.Watchlist:贵州、云南 / Footnote:EBITDA/ Interest2.7x`
- `rapidocr-auto-local` on `pdf-challenge`: `城投债 Credit Update / Q1 2026 风险提示 45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%／watchlist / 2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn / 2026年城投平台再融资跟踪 / Left Column / Right Column / `
- `rapidocr-auto-local` on `docx-challenge`: `城投债 Credit Update / Q1 2026 风险提示 45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%／watchlist / 2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn / 2026年城投平台再融资跟踪 / Left Column / Right Column / `
- `rapidocr-auto-local` on `pptx-challenge`: `城投债 Credit Update / Q1 2026 风险提示 45.2% / 并表口径Revenue1.28bn / 现金回收率93.4%／watchlist /  2 / 2026Q1到期分布8.2bn / AA+／城投平台／债务久期3.4y / 项目 / 数值 / 票息 / 4.52% / 主体评级 / AA+ / 债券余额 / 38.6bn /  3 / 2026年城投平台再融资跟踪 / Left Column / Right`
- `easyocr-auto-local` on `image-clean`: ``
- `easyocr-auto-local` on `image-low-contrast`: ``
- `easyocr-auto-local` on `image-rotated`: ``
- `easyocr-auto-local` on `image-table`: ``
- `easyocr-auto-local` on `image-dense-columns`: ``
- `easyocr-auto-local` on `pdf-challenge`: ``
- `easyocr-auto-local` on `docx-challenge`: ``
- `easyocr-auto-local` on `pptx-challenge`: ``
- `onnxtr-auto-local` on `image-clean`: `tetXI Credit Update / Q1 2026 IXSIET 45.2%`
- `onnxtr-auto-local` on `image-low-contrast`: `HEAR Revenue 1.28bn / IROKE 93.4% / watchlist`
- `onnxtr-auto-local` on `image-rotated`: `EINAST5 8.2bn / 202601 / 3.4y / / 5X X - B / 13ANB / AA+`
- `onnxtr-auto-local` on `image-table`: `* / L / 2 Z1E / E / à / 4.52% /  - / ERIY / AA+ / i T / 38.6bn`
- `onnxtr-auto-local` on `image-dense-columns`: `20261 / DE / Left Column / Right Column / 1. HRIL -2.3bn / A. DULEEEN AA+ / 2. HFTTER 17.4% / B. LHAZAAH 19.6F / 3. E I T EAIL6 1.18x / C. Watchlist: EN IF / Footnote: EBITDA / Interest 2.7x`
- `onnxtr-auto-local` on `pdf-challenge`: `tetXI Credit Update / Q1 2026 IXSIET 45.2% / HEAR Revenue 1.28bn / IROKE 93.4% / watchlist / EINAST5 8.2bn / 202601 / 3.4y / / 5X X - B / 13ANB / AA+ / mE / E / RE / 4.52% / EI / AA+ /  A EU / 38.6bn / 20261 / Left Colum`
- `onnxtr-auto-local` on `docx-challenge`: `tetXI Credit Update / Q1 2026 IXSIET 45.2% / HEAR Revenue 1.28bn / IROKE 93.4% / watchlist / EINAST5 8.2bn / 202601 / 3.4y / / 5X X - B / 13ANB / AA+ / * / L / 2 Z1E / E / à / 4.52% /  - / ERIY / AA+ / i T / 38.6bn / 202`
- `onnxtr-auto-local` on `pptx-challenge`: `tetXI Credit Update / Q1 2026 IXSIET 45.2% / HEAR Revenue 1.28bn / IROKE 93.4% / watchlist /  2 / EINAST5 8.2bn / 202601 / 3.4y / / 5X X - B / 13ANB / AA+ / * / L / 2 Z1E / E / à / 4.52% /  - / ERIY / AA+ / i T / 38.6bn `

## Raw JSON

```json
{
  "environment": {
    "generated_at": "2026-04-03T05:32:26.556960+00:00",
    "host": "Dereks-MacBook-Air-13.local",
    "python": "3.12.11"
  },
  "rows": [
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "image-clean",
      "ocr_status": "succeeded",
      "elapsed_ms": 1609.73,
      "score": 1.0,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "image-low-contrast",
      "ocr_status": "succeeded",
      "elapsed_ms": 2093.62,
      "score": 1.0,
      "ocr_text": "并表口径Revenue1.28bn\n现金回收率93.4%／watchlist",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "image-rotated",
      "ocr_status": "succeeded",
      "elapsed_ms": 1540.64,
      "score": 1.0,
      "ocr_text": "2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "image-table",
      "ocr_status": "succeeded",
      "elapsed_ms": 2021.23,
      "score": 1.0,
      "ocr_text": "项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "image-dense-columns",
      "ocr_status": "succeeded",
      "elapsed_ms": 1328.02,
      "score": 0.7459,
      "ocr_text": "2026年城投平台再融资跟踪\nLeft Column\nRight Column\n1.净融资-2.3bn\nA.债项评级维持AA+\n2.非标压降17.4%\nB.土储去化周期19.6月\n3.平台现金短债比1.18x\nC.Watchlist:贵州、云南\nFootnote:EBITDA/ Interest2.7x",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "pdf-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 8866.22,
      "score": 0.8675,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%／watchlist\n2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn\n2026年城投平台再融资跟踪\nLeft Column\nRight Column\n1.净融资-2.3bn\nA.债项评级维持AA+\n2.非标压降17.4%\nB.土储去化周期19.6月\n3.平台现金短债比1.18x\nC.Watchlist:贵州、云南\nFootnote:EBITDA/Interest 2.7x",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "docx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 9242.71,
      "score": 0.8675,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%／watchlist\n2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn\n2026年城投平台再融资跟踪\nLeft Column\nRight Column\n1.净融资-2.3bn\nA.债项评级维持AA+\n2.非标压降17.4%\nB.土储去化周期19.6月\n3.平台现金短债比1.18x\nC.Watchlist:贵州、云南\nFootnote:EBITDA/ Interest2.7x",
      "warnings": []
    },
    {
      "engine": "rapidocr-auto-local",
      "kind": "direct",
      "fixture": "pptx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 8334.81,
      "score": 0.8638,
      "ocr_text": "城投债 Credit Update\nQ1 2026 风险提示 45.2%\n并表口径Revenue1.28bn\n现金回收率93.4%／watchlist\n 2\n2026Q1到期分布8.2bn\nAA+／城投平台／债务久期3.4y\n项目\n数值\n票息\n4.52%\n主体评级\nAA+\n债券余额\n38.6bn\n 3\n2026年城投平台再融资跟踪\nLeft Column\nRight Column\n1.净融资-2.3bn\nA.债项评级维持AA+\n2.非标压降17.4%\nB.土储去化周期19.6月\n3.平台现金短债比1.18x\nC.Watchlist:贵州、云南\nFootnote:EBITDA/ Interest2.7x",
      "warnings": []
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "image-clean",
      "ocr_status": "failed",
      "elapsed_ms": 132.23,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-clean.png"
      ]
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "image-low-contrast",
      "ocr_status": "failed",
      "elapsed_ms": 685.49,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-low-contrast.png"
      ]
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "image-rotated",
      "ocr_status": "failed",
      "elapsed_ms": 381.5,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-rotated.png"
      ]
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "image-table",
      "ocr_status": "failed",
      "elapsed_ms": 177.73,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-table.png"
      ]
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "image-dense-columns",
      "ocr_status": "failed",
      "elapsed_ms": 1226.87,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "DocumentConversionError: OCR produced no usable text for challenge-dense-columns.png"
      ]
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "pdf-challenge",
      "ocr_status": "failed",
      "elapsed_ms": 1780.87,
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
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "docx-challenge",
      "ocr_status": "failed",
      "elapsed_ms": 1211.49,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2",
        "OCR returned no text for embedded image 3",
        "OCR returned no text for embedded image 4",
        "OCR returned no text for embedded image 5"
      ]
    },
    {
      "engine": "easyocr-auto-local",
      "kind": "direct",
      "fixture": "pptx-challenge",
      "ocr_status": "failed",
      "elapsed_ms": 1208.98,
      "score": 0.0,
      "ocr_text": "",
      "warnings": [
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2",
        "OCR returned no text for embedded image 1",
        "OCR returned no text for embedded image 2",
        "OCR returned no text for embedded image 1"
      ]
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "image-clean",
      "ocr_status": "succeeded",
      "elapsed_ms": 185.08,
      "score": 0.7,
      "ocr_text": "tetXI Credit Update\nQ1 2026 IXSIET 45.2%",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "image-low-contrast",
      "ocr_status": "succeeded",
      "elapsed_ms": 208.31,
      "score": 0.7273,
      "ocr_text": "HEAR Revenue 1.28bn\nIROKE 93.4% / watchlist",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "image-rotated",
      "ocr_status": "succeeded",
      "elapsed_ms": 881.57,
      "score": 0.2759,
      "ocr_text": "EINAST5 8.2bn\n202601\n3.4y\n/ 5X X - B / 13ANB\nAA+",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "image-table",
      "ocr_status": "succeeded",
      "elapsed_ms": 5987.4,
      "score": 0.4255,
      "ocr_text": "*\nL\n2 Z1E\nE\nà\n4.52%\n -\nERIY\nAA+\ni T\n38.6bn",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "image-dense-columns",
      "ocr_status": "succeeded",
      "elapsed_ms": 2125.66,
      "score": 0.5514,
      "ocr_text": "20261\nDE\nLeft Column\nRight Column\n1. HRIL -2.3bn\nA. DULEEEN AA+\n2. HFTTER 17.4%\nB. LHAZAAH 19.6F\n3. E I T EAIL6 1.18x\nC. Watchlist: EN IF\nFootnote: EBITDA / Interest 2.7x",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "pdf-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 13911.93,
      "score": 0.3715,
      "ocr_text": "tetXI Credit Update\nQ1 2026 IXSIET 45.2%\nHEAR Revenue 1.28bn\nIROKE 93.4% / watchlist\nEINAST5 8.2bn\n202601\n3.4y\n/ 5X X - B / 13ANB\nAA+\nmE\nE\nRE\n4.52%\nEI\nAA+\n A EU\n38.6bn\n20261\nLeft Column\nRight Column\n1. HRABI -2.3bn\nA. MTH AA+\n2. TEER 17.4%\nB. tAZIAN 19.6F\n3. TAMAULL 1.18x\nC. Watchlist: BAN, ZF\nFootnote: EBITDA / Interest 2.7x",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "docx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 2816.67,
      "score": 0.4051,
      "ocr_text": "tetXI Credit Update\nQ1 2026 IXSIET 45.2%\nHEAR Revenue 1.28bn\nIROKE 93.4% / watchlist\nEINAST5 8.2bn\n202601\n3.4y\n/ 5X X - B / 13ANB\nAA+\n*\nL\n2 Z1E\nE\nà\n4.52%\n -\nERIY\nAA+\ni T\n38.6bn\n20261\nDE\nLeft Column\nRight Column\n1. HRIL -2.3bn\nA. DULEEEN AA+\n2. HFTTER 17.4%\nB. LHAZAAH 19.6F\n3. E I T EAIL6 1.18x\nC. Watchlist: EN IF\nFootnote: EBITDA / Interest 2.7x",
      "warnings": []
    },
    {
      "engine": "onnxtr-auto-local",
      "kind": "direct",
      "fixture": "pptx-challenge",
      "ocr_status": "succeeded",
      "elapsed_ms": 5307.78,
      "score": 0.4076,
      "ocr_text": "tetXI Credit Update\nQ1 2026 IXSIET 45.2%\nHEAR Revenue 1.28bn\nIROKE 93.4% / watchlist\n 2\nEINAST5 8.2bn\n202601\n3.4y\n/ 5X X - B / 13ANB\nAA+\n*\nL\n2 Z1E\nE\nà\n4.52%\n -\nERIY\nAA+\ni T\n38.6bn\n 3\n20261\nDE\nLeft Column\nRight Column\n1. HRIL -2.3bn\nA. DULEEEN AA+\n2. HFTTER 17.4%\nB. LHAZAAH 19.6F\n3. E I T EAIL6 1.18x\nC. Watchlist: EN IF\nFootnote: EBITDA / Interest 2.7x",
      "warnings": []
    }
  ]
}
```
