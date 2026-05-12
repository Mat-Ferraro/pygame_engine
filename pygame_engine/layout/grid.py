"""
layout/grid.py

Grid layout helper for pygame_engine.

Distributes items into a uniform grid of rows and columns within a
bounds rect. All cells are the same size in v1 (uniform cell sizing).
Mixed fixed/weighted column sizing is a future expansion.

Usage::

    from pygame_engine.layout.grid import grid

    # 12 items in a 4-column grid with 8px gaps
    rects = grid(bounds, columns=4, count=12, item_size=(100, 80), spacing=8)
    for rect, item in zip(rects, items):
        item.set_rect(rect)
"""

from __future__ import annotations

import pygame


def grid(
    bounds: pygame.Rect,
    columns: int,
    count: int,
    item_size: tuple[int, int],
    spacing: int = 0,
    padding: int = 0,
) -> list[pygame.Rect]:
    """
    Distribute ``count`` items into a uniform grid within ``bounds``.

    Items fill left-to-right, top-to-bottom. The last row may be
    partially filled if ``count`` is not a multiple of ``columns``.

    All cells are the same size (``item_size``). The grid block is
    centred within the padded bounds.

    Args:
        bounds:    The available area to lay out within.
        columns:   Number of columns in the grid.
        count:     Total number of items to place.
        item_size: (width, height) of each cell.
        spacing:   Pixels between adjacent cells (horizontal and vertical).
        padding:   Inward margin on all four sides of ``bounds``.

    Returns:
        List of ``pygame.Rect`` objects, one per item, row by row.
        Returns an empty list when ``count`` is zero.

    Raises:
        ValueError: If ``columns`` is less than 1 or ``count`` is negative.
    """
    if columns < 1:
        raise ValueError(f"columns must be >= 1, got {columns}")
    if count < 0:
        raise ValueError(f"count must be >= 0, got {count}")
    if count == 0:
        return []

    iw, ih = item_size
    rows = (count + columns - 1) // columns  # ceiling division

    inner = bounds.inflate(-padding * 2, -padding * 2)

    grid_w = iw * columns + spacing * (columns - 1)
    grid_h = ih * rows    + spacing * (rows - 1)

    # Centre the grid block within the padded bounds
    start_x = inner.x + (inner.width  - grid_w) // 2
    start_y = inner.y + (inner.height - grid_h) // 2

    rects: list[pygame.Rect] = []
    for i in range(count):
        col = i % columns
        row = i // columns
        x = start_x + col * (iw + spacing)
        y = start_y + row * (ih + spacing)
        rects.append(pygame.Rect(x, y, iw, ih))

    return rects
