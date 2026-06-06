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
