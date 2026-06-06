# Vertical OCR Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the OCR provider automatically return readable text for traditional vertical Chinese pages while preserving existing horizontal OCR output behavior.

**Architecture:** RapidOCR will continue to perform detection and recognition. The provider will preserve RapidOCR's structured `box + text + confidence` output as `OcrTextBlock` values, then run a small reading-order postprocessor that leaves horizontal pages in original engine order and reorders detected vertical pages from right to left. This keeps API responses unchanged while improving the `text` field.

**Tech Stack:** Python 3.12, dataclasses, unittest, RapidOCR ONNX Runtime, FastAPI provider models.

---

## Scope Check

This plan covers one subsystem: OCR text reading-order postprocessing for provider outputs. It does not change the public `/v1/ocr` response schema, install new OCR engines, repair CUDA/cuDNN, or add full document layout analysis for tables and multi-column horizontal documents.

## File Structure

- Create `provider/layout.py`: owns OCR text-block geometry, vertical-page detection, footer filtering, and final text rendering.
- Modify `provider/config.py`: adds `OCR_LAYOUT_MODE` and `OCR_LAYOUT_DROP_FOOTER` environment settings.
- Modify `provider/engines.py`: adds `blocks` to `EngineOcrResult`, has `RapidOcrEngine` preserve raw OCR blocks, and calls the layout renderer to produce `text`.
- Keep `provider/app.py` response models unchanged. PDF OCR already calls `OcrRuntime.ocr_image()`, so page text will receive postprocessed text automatically.
- Keep `provider/gpu_worker.py` response schema unchanged. The worker builds `RapidOcrEngine`, so it returns postprocessed `text` without additional worker protocol changes.
- Create `tests/test_layout_postprocess.py`: unit tests for horizontal preservation, vertical detection, right-to-left ordering, footer dropping, and explicit layout modes.
- Create `tests/test_rapidocr_layout_integration.py`: integration-style unit test with a fake RapidOCR engine to verify `RapidOcrEngine.ocr_image()` uses the postprocessor.

## Task 1: Add Layout Postprocessor

**Files:**
- Create: `provider/layout.py`
- Test: `tests/test_layout_postprocess.py`

- [ ] **Step 1: Write failing tests for layout behavior**

Create `tests/test_layout_postprocess.py` with this complete content:

```python
from __future__ import annotations

import unittest

from provider.layout import OcrTextBlock, detect_layout, render_text_blocks


def block(text: str, left: float, top: float, right: float, bottom: float, confidence: float = 0.9) -> OcrTextBlock:
    return OcrTextBlock(
        text=text,
        bbox=[
            [left, top],
            [right, top],
            [right, bottom],
            [left, bottom],
        ],
        confidence=confidence,
    )


class LayoutPostprocessTests(unittest.TestCase):
    def test_horizontal_mode_preserves_engine_order(self) -> None:
        blocks = [
            block("second in geometry but first from engine", 200, 40, 260, 60),
            block("first in geometry but second from engine", 10, 10, 100, 30),
        ]

        text = render_text_blocks(blocks, mode="auto", drop_footer=True)

        self.assertEqual(
            text,
            "second in geometry but first from engine\nfirst in geometry but second from engine",
        )

    def test_detects_vertical_when_most_blocks_are_tall_columns(self) -> None:
        blocks = [
            block("right 1", 550, 100, 580, 850),
            block("right 2", 520, 110, 545, 820),
            block("middle 1", 470, 100, 500, 850),
            block("middle 2", 430, 100, 460, 850),
            block("left 1", 390, 100, 420, 850),
            block("footer", 350, 930, 620, 950),
        ]

        self.assertEqual(detect_layout(blocks), "vertical")

    def test_vertical_auto_orders_columns_from_right_to_left(self) -> None:
        blocks = [
            block("left column", 80, 100, 110, 850),
            block("right column", 540, 100, 570, 850),
            block("middle column", 280, 100, 310, 850),
        ]

        text = render_text_blocks(blocks, mode="auto", drop_footer=True)

        self.assertEqual(text, "right column\nmiddle column\nleft column")

    def test_vertical_auto_orders_same_column_from_top_to_bottom(self) -> None:
        blocks = [
            block("right lower", 540, 450, 570, 850),
            block("right upper", 540, 100, 570, 400),
            block("left upper", 280, 100, 310, 400),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=True)

        self.assertEqual(text, "right upper\nright lower\nleft upper")

    def test_vertical_drops_horizontal_footer_when_enabled(self) -> None:
        blocks = [
            block("正文右列", 540, 100, 570, 850),
            block("正文左列", 280, 100, 310, 850),
            block("前言·EFT解開愛情之舞的|16", 350, 930, 620, 950),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=True)

        self.assertEqual(text, "正文右列\n正文左列")

    def test_vertical_keeps_horizontal_footer_when_disabled(self) -> None:
        blocks = [
            block("正文右列", 540, 100, 570, 850),
            block("正文左列", 280, 100, 310, 850),
            block("前言·EFT解開愛情之舞的|16", 350, 930, 620, 950),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=False)

        self.assertEqual(text, "正文右列\n正文左列\n前言·EFT解開愛情之舞的|16")

    def test_explicit_horizontal_mode_preserves_engine_order_even_for_vertical_geometry(self) -> None:
        blocks = [
            block("engine first left", 80, 100, 110, 850),
            block("engine second right", 540, 100, 570, 850),
        ]

        text = render_text_blocks(blocks, mode="horizontal", drop_footer=True)

        self.assertEqual(text, "engine first left\nengine second right")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m unittest tests.test_layout_postprocess -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'provider.layout'`.

- [ ] **Step 3: Implement the layout postprocessor**

Create `provider/layout.py` with this complete content:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LayoutMode = Literal["auto", "horizontal", "vertical", "none"]
DetectedLayout = Literal["horizontal", "vertical"]


@dataclass(frozen=True)
class OcrTextBlock:
    text: str
    bbox: list[list[float]]
    confidence: float | None = None


def render_text_blocks(
    blocks: list[OcrTextBlock],
    *,
    mode: LayoutMode = "auto",
    drop_footer: bool = True,
) -> str:
    normalized = [block for block in blocks if block.text.strip()]
    if mode == "none":
        return "\n".join(block.text.strip() for block in normalized).strip()
    if mode == "horizontal":
        return "\n".join(block.text.strip() for block in normalized).strip()

    layout = detect_layout(normalized) if mode == "auto" else "vertical"
    if layout == "horizontal":
        return "\n".join(block.text.strip() for block in normalized).strip()

    page_width, page_height = _page_size(normalized)
    ordered = []
    for block in normalized:
        if drop_footer and _is_horizontal_footer(block, page_height):
            continue
        if drop_footer and not _is_vertical_block(block):
            continue
        ordered.append(block)
    ordered.sort(key=lambda block: (-_center(block)[0], _center(block)[1]))
    return "\n".join(block.text.strip() for block in ordered).strip()


def detect_layout(blocks: list[OcrTextBlock]) -> DetectedLayout:
    if not blocks:
        return "horizontal"
    vertical_count = sum(1 for block in blocks if _is_vertical_block(block))
    if vertical_count >= 5 and vertical_count >= len(blocks) * 0.55:
        return "vertical"
    return "horizontal"


def _center(block: OcrTextBlock) -> tuple[float, float]:
    xs = [point[0] for point in block.bbox]
    ys = [point[1] for point in block.bbox]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _size(block: OcrTextBlock) -> tuple[float, float]:
    xs = [point[0] for point in block.bbox]
    ys = [point[1] for point in block.bbox]
    return max(xs) - min(xs), max(ys) - min(ys)


def _page_size(blocks: list[OcrTextBlock]) -> tuple[float, float]:
    max_x = 0.0
    max_y = 0.0
    for block in blocks:
        for x, y in block.bbox:
            max_x = max(max_x, float(x))
            max_y = max(max_y, float(y))
    return max_x, max_y


def _is_vertical_block(block: OcrTextBlock) -> bool:
    width, height = _size(block)
    return height > width * 4


def _is_horizontal_footer(block: OcrTextBlock, page_height: float) -> bool:
    if page_height <= 0:
        return False
    width, height = _size(block)
    _center_x, center_y = _center(block)
    return width > height * 3 and center_y > page_height * 0.88
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
.venv/bin/python -m unittest tests.test_layout_postprocess -v
```

Expected: PASS, 7 tests.

- [ ] **Step 5: Commit checkpoint if the workspace is a git repo**

Run:

```bash
git rev-parse --is-inside-work-tree
```

Expected in this workspace may be `fatal: not a git repository`. If it prints `true`, run:

```bash
git add provider/layout.py tests/test_layout_postprocess.py
git commit -m "feat: add OCR layout postprocessor"
```

## Task 2: Add Layout Configuration

**Files:**
- Modify: `provider/config.py`
- Test: `tests/test_layout_postprocess.py`

- [ ] **Step 1: Add failing tests for environment configuration**

Append this test class to `tests/test_layout_postprocess.py` before the `if __name__ == "__main__":` block:

```python
import os
from contextlib import ExitStack
from unittest.mock import patch

from provider.config import Settings


class LayoutConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_stack = ExitStack()
        env = {
            "OCR_PROVIDER": "rapidocr",
            "OCR_MODEL": "rapidocr:ch_sim+en",
            "OCR_LANGUAGES": "ch_sim,en",
            "OCR_DEVICE": "cpu",
        }
        for key, value in env.items():
            self._env_stack.enter_context(patch.dict(os.environ, {key: value}))

    def tearDown(self) -> None:
        self._env_stack.close()

    def test_layout_defaults_to_auto_and_footer_drop_enabled(self) -> None:
        settings = Settings.from_env()

        self.assertEqual(settings.ocr_layout_mode, "auto")
        self.assertTrue(settings.ocr_layout_drop_footer)

    def test_layout_env_overrides_are_read(self) -> None:
        with patch.dict(os.environ, {"OCR_LAYOUT_MODE": "vertical", "OCR_LAYOUT_DROP_FOOTER": "false"}):
            settings = Settings.from_env()

        self.assertEqual(settings.ocr_layout_mode, "vertical")
        self.assertFalse(settings.ocr_layout_drop_footer)

    def test_invalid_layout_mode_falls_back_to_auto(self) -> None:
        with patch.dict(os.environ, {"OCR_LAYOUT_MODE": "diagonal"}):
            settings = Settings.from_env()

        self.assertEqual(settings.ocr_layout_mode, "auto")
```

- [ ] **Step 2: Run tests to verify config fields are missing**

Run:

```bash
.venv/bin/python -m unittest tests.test_layout_postprocess.LayoutConfigTests -v
```

Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'ocr_layout_mode'`.

- [ ] **Step 3: Add settings fields and parser**

Modify `provider/config.py`.

Add this helper after `_env_languages`:

```python
def _env_layout_mode(name: str, default: str) -> str:
    value = os.getenv(name)
    normalized = str(value or default).strip().lower()
    if normalized in {"auto", "horizontal", "vertical", "none"}:
        return normalized
    return default
```

Add these fields to the `Settings` dataclass after `render_scale: float`:

```python
    ocr_layout_mode: str
    ocr_layout_drop_footer: bool
```

Add these values in `Settings.from_env()` after `render_scale=float(os.getenv("PDF_RENDER_SCALE", "2.0")),`:

```python
            ocr_layout_mode=_env_layout_mode("OCR_LAYOUT_MODE", "auto"),
            ocr_layout_drop_footer=_env_bool("OCR_LAYOUT_DROP_FOOTER", True),
```

- [ ] **Step 4: Run config tests to verify they pass**

Run:

```bash
.venv/bin/python -m unittest tests.test_layout_postprocess.LayoutConfigTests -v
```

Expected: PASS, 3 tests.

- [ ] **Step 5: Run all layout tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_layout_postprocess -v
```

Expected: PASS, 10 tests.

- [ ] **Step 6: Commit checkpoint if the workspace is a git repo**

Run:

```bash
git rev-parse --is-inside-work-tree
```

Expected in this workspace may be `fatal: not a git repository`. If it prints `true`, run:

```bash
git add provider/config.py tests/test_layout_postprocess.py
git commit -m "feat: configure OCR layout postprocessing"
```

## Task 3: Preserve RapidOCR Blocks and Render Text Through Layout Layer

**Files:**
- Modify: `provider/engines.py`
- Test: `tests/test_rapidocr_layout_integration.py`

- [ ] **Step 1: Write failing RapidOCR integration tests**

Create `tests/test_rapidocr_layout_integration.py` with this complete content:

```python
from __future__ import annotations

import io
import os
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from PIL import Image

from provider.config import Settings
from provider.engines import RapidOcrEngine


def png_bytes() -> bytes:
    image = Image.new("RGB", (20, 20), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class FakeRapidEngine:
    def __init__(self, result: list[list[object]]) -> None:
        self.result = result

    def __call__(self, _image):
        return self.result, 0.01


class RapidOcrLayoutIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_stack = ExitStack()
        env = {
            "OCR_PROVIDER": "rapidocr",
            "OCR_MODEL": "rapidocr:ch_sim+en",
            "OCR_LANGUAGES": "ch_sim,en",
            "OCR_DEVICE": "cpu",
            "OCR_LAYOUT_MODE": "auto",
            "OCR_LAYOUT_DROP_FOOTER": "true",
        }
        for key, value in env.items():
            self._env_stack.enter_context(patch.dict(os.environ, {key: value}))

    def tearDown(self) -> None:
        self._env_stack.close()

    def make_engine(self, result: list[list[object]]) -> RapidOcrEngine:
        engine = RapidOcrEngine.__new__(RapidOcrEngine)
        engine._settings = Settings.from_env()
        engine._engine = FakeRapidEngine(result)
        engine.provider_name = "rapidocr"
        engine.model_id = "rapidocr:ch_sim+en"
        engine.device_name = "cpu"
        return engine

    def test_horizontal_output_matches_rapidocr_result_order(self) -> None:
        result = [
            [[[200.0, 40.0], [260.0, 40.0], [260.0, 60.0], [200.0, 60.0]], "engine first", 0.91],
            [[[10.0, 10.0], [100.0, 10.0], [100.0, 30.0], [10.0, 30.0]], "engine second", 0.81],
        ]
        engine = self.make_engine(result)

        ocr_result = engine.ocr_image(png_bytes())

        self.assertEqual(ocr_result.text, "engine first\nengine second")
        self.assertEqual(len(ocr_result.blocks), 2)
        self.assertAlmostEqual(ocr_result.confidence or 0.0, 0.86)

    def test_vertical_output_is_reordered_from_right_to_left(self) -> None:
        result = [
            [[[80.0, 100.0], [110.0, 100.0], [110.0, 850.0], [80.0, 850.0]], "left column", 0.91],
            [[[540.0, 100.0], [570.0, 100.0], [570.0, 850.0], [540.0, 850.0]], "right column", 0.92],
            [[[280.0, 100.0], [310.0, 100.0], [310.0, 850.0], [280.0, 850.0]], "middle column", 0.93],
            [[[350.0, 930.0], [620.0, 930.0], [620.0, 950.0], [350.0, 950.0]], "footer|16", 0.80],
            [[[500.0, 100.0], [530.0, 100.0], [530.0, 850.0], [500.0, 850.0]], "right middle", 0.94],
            [[[450.0, 100.0], [480.0, 100.0], [480.0, 850.0], [450.0, 850.0]], "middle right", 0.95],
        ]
        engine = self.make_engine(result)

        ocr_result = engine.ocr_image(png_bytes())

        self.assertEqual(
            ocr_result.text,
            "right column\nright middle\nmiddle right\nmiddle column\nleft column",
        )
        self.assertEqual(len(ocr_result.blocks), 6)
```

- [ ] **Step 2: Run tests to verify `blocks` support is missing**

Run:

```bash
.venv/bin/python -m unittest tests.test_rapidocr_layout_integration -v
```

Expected: FAIL with `AttributeError: 'EngineOcrResult' object has no attribute 'blocks'` or vertical text in original engine order.

- [ ] **Step 3: Add block support to engine result types**

Modify the top of `provider/engines.py`.

Add this import after `from provider.config import Settings`:

```python
from provider.layout import OcrTextBlock, render_text_blocks
```

Replace `EngineOcrResult` with:

```python
@dataclass
class EngineOcrResult:
    text: str
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)
    blocks: list[OcrTextBlock] = field(default_factory=list)
```

- [ ] **Step 4: Update RapidOCR text assembly**

Replace `RapidOcrEngine.ocr_image()` in `provider/engines.py` with:

```python
    def ocr_image(self, data: bytes) -> EngineOcrResult:
        result, _elapsed = self._engine(self._image_from_bytes(data))
        blocks: list[OcrTextBlock] = []
        confidences: list[float] = []
        for item in result or []:
            if len(item) < 3:
                continue
            text = str(item[1]).strip()
            if not text:
                continue
            confidence = None
            try:
                confidence = float(item[2])
                confidences.append(confidence)
            except (TypeError, ValueError):
                confidence = None
            raw_box = item[0]
            box = [[float(point[0]), float(point[1])] for point in raw_box]
            blocks.append(OcrTextBlock(text=text, bbox=box, confidence=confidence))
        confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
        text = render_text_blocks(
            blocks,
            mode=self._settings.ocr_layout_mode,
            drop_footer=self._settings.ocr_layout_drop_footer,
        )
        return EngineOcrResult(text=text, confidence=confidence, blocks=blocks)
```

- [ ] **Step 5: Run RapidOCR integration tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_rapidocr_layout_integration -v
```

Expected: PASS, 2 tests.

- [ ] **Step 6: Run existing admission/offload tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_admission_controller -v
```

Expected: PASS. If `FakeWorker.ocr_image()` returning plain `object()` causes a new type issue, no change is expected because those tests do not inspect OCR text.

- [ ] **Step 7: Commit checkpoint if the workspace is a git repo**

Run:

```bash
git rev-parse --is-inside-work-tree
```

Expected in this workspace may be `fatal: not a git repository`. If it prints `true`, run:

```bash
git add provider/engines.py tests/test_rapidocr_layout_integration.py
git commit -m "feat: apply layout postprocessing to RapidOCR"
```

## Task 4: Document Runtime Behavior and Verify Full Test Suite

**Files:**
- Modify: `README.md`
- Test: all unit tests

- [ ] **Step 1: Add README documentation**

Add this section to `README.md` after the existing production defaults section that lists `rapidocr` support:

```markdown
## Layout postprocessing

RapidOCR returns detected text boxes in a horizontal reading order by default: top-to-bottom, left-to-right. The provider keeps that behavior for normal horizontal pages, then applies a small reading-order postprocessor when a page is detected as traditional vertical text.

Configuration:

- `OCR_LAYOUT_MODE=auto`: default. Preserve RapidOCR order for horizontal pages and reorder vertical pages right-to-left.
- `OCR_LAYOUT_MODE=horizontal`: always preserve RapidOCR result order.
- `OCR_LAYOUT_MODE=vertical`: always sort text blocks right-to-left, then top-to-bottom.
- `OCR_LAYOUT_MODE=none`: join raw OCR text blocks in the engine result order without layout detection.
- `OCR_LAYOUT_DROP_FOOTER=true`: default. In vertical mode, drop horizontal footer/page-number blocks near the bottom of the page.

This changes only the returned `text` content. The `/v1/ocr` response schema is unchanged.
```

- [ ] **Step 2: Run focused layout tests**

Run:

```bash
.venv/bin/python -m unittest tests.test_layout_postprocess tests.test_rapidocr_layout_integration -v
```

Expected: PASS, 12 tests.

- [ ] **Step 3: Run all tests**

Run:

```bash
.venv/bin/python -m unittest discover tests -v
```

Expected: PASS for all tests.

- [ ] **Step 4: Manually verify the known vertical PDF sample if available**

Run:

```bash
OCR_PROVIDER=rapidocr OCR_MODEL=rapidocr:ch_sim+en OCR_LANGUAGES=ch_sim,en OCR_DEVICE=cpu OCR_MODEL_STORAGE_DIR=./runtime-cache/rapidocr-zh-en \
.venv/bin/python scripts/convert_pdf_to_markdown.py \
'/Users/stardust/Downloads/抱紧我  扭转夫妻关系的七种对话_蘇珊·强森.pdf' \
'/tmp/hold-me-pages-20-22-after-service-layout.md' \
--pages 20-22 \
--title '抱紧我 扭转夫妻关系的七种对话' \
--layout auto
```

Expected: output starts page 20 from the rightmost vertical column, not from the leftmost column. If the file is unavailable on the worker's machine, skip this manual check and rely on unit tests.

- [ ] **Step 5: Commit final checkpoint if the workspace is a git repo**

Run:

```bash
git rev-parse --is-inside-work-tree
```

Expected in this workspace may be `fatal: not a git repository`. If it prints `true`, run:

```bash
git add README.md provider/config.py provider/engines.py provider/layout.py tests/test_layout_postprocess.py tests/test_rapidocr_layout_integration.py
git commit -m "docs: document OCR layout postprocessing"
```

## Self-Review

Spec coverage:

- Automatic vertical adaptation is implemented by `detect_layout()` and `render_text_blocks()`.
- RapidOCR output is preserved as structured blocks before text rendering.
- Existing horizontal output is preserved by keeping engine order for horizontal/auto-horizontal pages.
- The public API schema remains unchanged.
- GPU worker behavior is covered because it uses `build_engine()` and receives postprocessed `result.text`.

Placeholder scan:

- No task uses TBD, TODO, “similar to”, or undefined functions.
- Each code-changing step includes exact code to add or replace.

Type consistency:

- `OcrTextBlock`, `LayoutMode`, `detect_layout()`, and `render_text_blocks()` are defined in Task 1 and reused consistently in later tasks.
- `Settings.ocr_layout_mode` and `Settings.ocr_layout_drop_footer` are defined in Task 2 before Task 3 uses them.
- `EngineOcrResult.blocks` is defined in Task 3 before tests assert on it.
