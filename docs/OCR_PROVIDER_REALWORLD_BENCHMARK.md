# OCR Provider Real-World Benchmark

- Generated on: 2026-04-03
- Host: `Dereks-MacBook-Air-13.local`
- Decision: production OCR standardizes on `rapidocr`

## Fixture

- Image under test: [`dfcfw-page1.png`](/Users/derek/Projects/memory-connector/scripts/realworld-fixtures/dfcfw-page1.png)
- Source PDF: [`dfcfw-pingan-analyst.pdf`](/Users/derek/Projects/memory-connector/scripts/realworld-fixtures/dfcfw-pingan-analyst.pdf)
- Ground truth: native text extracted from page 1 of the PDF with `pypdf`
- Score: normalized `SequenceMatcher` ratio between OCR output and the PDF-derived ground truth

## Findings

- `rapidocr` was the only lightweight engine that produced usable Chinese output on this real report page.
- On this macOS host, `OCR_DEVICE=auto` resolved `rapidocr` to `coreml`.
- `easyocr` on `mps` produced no usable text.
- `onnxtr` on `coreml` ran, but Chinese recognition quality was too poor for deployment.

## Engine Comparison

| Engine | Device (`auto`) | Score | Result |
| --- | --- | ---: | --- |
| `rapidocr` | `coreml` | `0.6866` | Usable |
| `easyocr` | `mps` | `0.0000` | Empty output |
| `onnxtr` | `coreml` | `0.0437` | Unusable Chinese text |

## RapidOCR Format Coverage

The same page image was exercised through the document pipeline as raw image / embedded PDF / DOCX / PPTX content.

| Path | Resolved device | Score | Elapsed (ms) |
| --- | --- | ---: | ---: |
| `image` | `coreml` | `0.6866` | `6350.89` |
| `pdf` | `coreml` | `0.6981` | `11564.22` |
| `docx` | `coreml` | `0.6866` | `9386.71` |
| `pptx` | `coreml` | `0.6866` | `5942.81` |

## Memory Notes

- Model/cache footprint on disk: about `47MB`
- Process RSS after engine init on macOS CoreML path: about `230.8MB`
- Process RSS after first inference on macOS CoreML path: about `360.6MB`

## GPU4 Remote Admission Benchmark

- Remote host: `stardust-gpu4`
- Remote runtime: `rapidocr + cuda`
- Endpoint under test: local bind `127.0.0.1:7998` on the host, avoiding Cloudflare edge effects
- Fixture: [`arxiv-screenshot.png`](/Users/derek/Projects/memory-connector/memory%20frameworks/graphiti/images/arxiv-screenshot.png)
- Admission config:
  - `OCR_MAX_CONCURRENCY=4`
  - `OCR_QUEUE_TIMEOUT_SECONDS=15`
  - `OCR_GPU_MIN_FREE_VRAM_MB=4096`
  - `OCR_GPU_PER_REQUEST_VRAM_MB=3072`

### Burst Result

`6` concurrent local requests against the live `gpu4` service produced:

| Metric | Value |
| --- | ---: |
| Total wall time | `1.737s` |
| Fast cohort latency | `1.178s` to `1.234s` |
| Queued cohort latency | `1.727s` to `1.736s` |
| Max `active_requests` | `4` |
| Max `queued_requests` | `2` |
| Min free VRAM observed | `22886MB` |
| Result status | `6/6` succeeded |

Interpretation:

- The service admitted exactly `4` in-flight requests, matching the configured ceiling.
- The extra `2` requests stayed queued until earlier requests completed.
- No request hit the `15s` timeout, so the service returned `200` for all `6`.
- Free VRAM stayed well above the `4096MB` reserve floor, so there was no OOM pressure during this burst.

## Sample Output

`rapidocr` excerpt:

```text
证券研究报告
华源证券
非银金融丨保险Ⅱ
金融|公司点评报告
HUAYUAN SECURITIES
2025年11月03日
中国平安(601318.SH)
投资评级：买入 (维持)
利润数据大幅增长，寿险NBV持续高增
投资要点：
```
