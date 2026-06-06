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
    def test_rejects_unsupported_layout_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported layout mode"):
            render_text_blocks([block("x", 10, 10, 20, 20)], mode="diagonal", drop_footer=True)

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

    def test_vertical_groups_same_column_with_small_x_jitter(self) -> None:
        blocks = [
            block("right lower with jitter", 544, 450, 574, 850),
            block("right upper", 540, 100, 570, 400),
            block("left upper", 280, 100, 310, 400),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=True)

        self.assertEqual(text, "right upper\nright lower with jitter\nleft upper")

    def test_vertical_drops_horizontal_footer_when_enabled(self) -> None:
        blocks = [
            block("正文右列", 540, 100, 570, 850),
            block("正文左列", 280, 100, 310, 850),
            block("前言·EFT解開愛情之舞的|16", 350, 930, 620, 950),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=True)

        self.assertEqual(text, "正文右列\n正文左列")

    def test_vertical_drops_standalone_page_number_when_enabled(self) -> None:
        blocks = [
            block("正文右列", 540, 100, 570, 850),
            block("正文左列", 280, 100, 310, 850),
            block("— 16 —", 590, 930, 610, 950),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=True)

        self.assertEqual(text, "正文右列\n正文左列")

    def test_vertical_keeps_non_footer_horizontal_content_when_drop_footer_enabled(self) -> None:
        blocks = [
            block("正文右列", 540, 100, 570, 850),
            block("正文左列", 280, 100, 310, 850),
            block("章節標題", 220, 40, 500, 70),
            block("中段註記", 120, 420, 360, 450),
            block("前言·EFT解開愛情之舞的|16", 350, 930, 620, 950),
        ]

        text = render_text_blocks(blocks, mode="vertical", drop_footer=True)

        self.assertEqual(text, "正文右列\n正文左列\n章節標題\n中段註記")

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


import os
from contextlib import ExitStack
from pathlib import Path
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
        self._env_stack.enter_context(patch.dict(os.environ, env, clear=True))

    def tearDown(self) -> None:
        self._env_stack.close()

    def test_layout_defaults_to_auto_and_footer_drop_enabled(self) -> None:
        settings = Settings.from_env()

        self.assertEqual(settings.ocr_layout_mode, "auto")
        self.assertTrue(settings.ocr_layout_drop_footer)

    def test_direct_settings_constructor_keeps_layout_defaults(self) -> None:
        settings = Settings(
            service_name="ocr-provider",
            ocr_provider="rapidocr",
            model_id="rapidocr:ch_sim+en",
            model_alias=None,
            api_key=None,
            ocr_languages=("ch_sim", "en"),
            ocr_device="cpu",
            paragraph=True,
            model_storage_dir=Path("runtime-cache/ocr"),
            render_scale=2.0,
            max_concurrency=4,
            queue_timeout_seconds=15.0,
            queue_poll_seconds=0.2,
            idle_offload_seconds=1800.0,
            idle_offload_poll_seconds=30.0,
            gpu_min_free_vram_mb=4096,
            gpu_per_request_vram_mb=3072,
            tesseract_cmd=None,
            paddle_text_detection_model_name=None,
            paddle_text_recognition_model_name=None,
            paddle_lang=None,
            paddle_use_doc_orientation_classify=False,
            paddle_use_doc_unwarping=False,
            paddle_use_textline_orientation=False,
            paddle_disable_model_source_check=True,
        )

        self.assertEqual(settings.ocr_layout_mode, "auto")
        self.assertIs(settings.ocr_layout_drop_footer, True)

    def test_layout_env_overrides_are_read(self) -> None:
        with patch.dict(os.environ, {"OCR_LAYOUT_MODE": "vertical", "OCR_LAYOUT_DROP_FOOTER": "false"}):
            settings = Settings.from_env()

        self.assertEqual(settings.ocr_layout_mode, "vertical")
        self.assertFalse(settings.ocr_layout_drop_footer)

    def test_invalid_layout_mode_falls_back_to_auto(self) -> None:
        with patch.dict(os.environ, {"OCR_LAYOUT_MODE": "diagonal"}):
            settings = Settings.from_env()

        self.assertEqual(settings.ocr_layout_mode, "auto")


if __name__ == "__main__":
    unittest.main()
