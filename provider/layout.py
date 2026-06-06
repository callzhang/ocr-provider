from __future__ import annotations

from dataclasses import dataclass
import re
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
    if mode not in ("auto", "horizontal", "vertical", "none"):
        raise ValueError(f"Unsupported layout mode: {mode!r}")

    normalized = [block for block in blocks if block.text.strip()]
    if mode == "none":
        return "\n".join(block.text.strip() for block in normalized).strip()
    if mode == "horizontal":
        return "\n".join(block.text.strip() for block in normalized).strip()

    layout = detect_layout(normalized) if mode == "auto" else "vertical"
    if layout == "horizontal":
        return "\n".join(block.text.strip() for block in normalized).strip()

    _page_width, page_height = _page_size(normalized)
    kept = []
    for block in normalized:
        if drop_footer and _is_horizontal_footer(block, page_height):
            continue
        kept.append(block)
    ordered = _order_vertical_layout(kept)
    return "\n".join(block.text.strip() for block in ordered).strip()


def detect_layout(blocks: list[OcrTextBlock]) -> DetectedLayout:
    if not blocks:
        return "horizontal"
    vertical_count = sum(1 for block in blocks if _is_vertical_block(block))
    if vertical_count >= 3 and vertical_count >= len(blocks) * 0.55:
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
    if center_y <= page_height * 0.88:
        return False
    return width > height * 3 or _is_page_number_marker(block.text)


def _is_page_number_marker(text: str) -> bool:
    stripped = text.strip()
    return re.fullmatch(r"[-\u2010-\u2015\s]*\d{1,4}[-\u2010-\u2015\s]*", stripped) is not None


def _order_vertical_layout(blocks: list[OcrTextBlock]) -> list[OcrTextBlock]:
    vertical_blocks = [block for block in blocks if _is_vertical_block(block)]
    other_blocks = [block for block in blocks if not _is_vertical_block(block)]
    ordered = _order_vertical_columns(vertical_blocks)
    ordered.extend(sorted(other_blocks, key=lambda block: (_center(block)[1], _center(block)[0])))
    return ordered


def _order_vertical_columns(blocks: list[OcrTextBlock]) -> list[OcrTextBlock]:
    columns: list[list[OcrTextBlock]] = []
    for block in sorted(blocks, key=lambda item: -_center(item)[0]):
        column = _find_column(columns, block)
        if column is None:
            columns.append([block])
        else:
            column.append(block)

    columns.sort(key=lambda column: -_column_center_x(column))
    ordered = []
    for column in columns:
        ordered.extend(sorted(column, key=lambda block: (_center(block)[1], _center(block)[0])))
    return ordered


def _find_column(columns: list[list[OcrTextBlock]], block: OcrTextBlock) -> list[OcrTextBlock] | None:
    center_x, _center_y = _center(block)
    width, _height = _size(block)
    tolerance = max(12.0, width * 0.75)
    for column in columns:
        column_widths = [_size(column_block)[0] for column_block in column]
        column_tolerance = max(tolerance, max(column_widths) * 0.75)
        if abs(center_x - _column_center_x(column)) <= column_tolerance:
            return column
    return None


def _column_center_x(column: list[OcrTextBlock]) -> float:
    return sum(_center(block)[0] for block in column) / len(column)
