"""
tests/test_layout.py

Tests for pygame_engine.layout — anchor, row, column, grid.

Covers: correct rect positions, spacing, padding, alignment, edge cases.
"""

import pygame

from pygame_engine.layout import anchor, column, grid, row


BOUNDS = pygame.Rect(0, 0, 600, 400)


# ── anchor ────────────────────────────────────────────────────────────────────

def test_anchor_center() -> None:
    r = anchor(BOUNDS, (100, 50), "center")
    assert r.centerx == BOUNDS.centerx
    assert r.centery == BOUNDS.centery
    assert r.width   == 100
    assert r.height  == 50


def test_anchor_top_left_with_margin() -> None:
    r = anchor(BOUNDS, (80, 40), "top_left", margin=10)
    assert r.x == 10
    assert r.y == 10


def test_anchor_bottom_right_with_margin() -> None:
    r = anchor(BOUNDS, (80, 40), "bottom_right", margin=10)
    assert r.right  == BOUNDS.right  - 10
    assert r.bottom == BOUNDS.bottom - 10


def test_anchor_top_center() -> None:
    r = anchor(BOUNDS, (100, 40), "top", margin=5)
    assert r.centerx == BOUNDS.centerx
    assert r.y       == 5


def test_anchor_bottom_center() -> None:
    r = anchor(BOUNDS, (100, 40), "bottom", margin=5)
    assert r.centerx == BOUNDS.centerx
    assert r.bottom  == BOUNDS.bottom - 5


def test_anchor_offset_applied() -> None:
    r = anchor(BOUNDS, (100, 50), "center", offset=(10, -20))
    assert r.centerx == BOUNDS.centerx + 10
    assert r.centery == BOUNDS.centery - 20


def test_anchor_invalid_point_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        anchor(BOUNDS, (100, 50), "invalid_point")


# ── row ───────────────────────────────────────────────────────────────────────

def test_row_returns_correct_count() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40))
    assert len(rects) == 3


def test_row_items_are_correct_size() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40))
    for r in rects:
        assert r.width  == 80
        assert r.height == 40


def test_row_items_evenly_spaced() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40), spacing=10)
    gap = rects[1].x - rects[0].right
    assert gap == 10
    gap2 = rects[2].x - rects[1].right
    assert gap2 == 10


def test_row_group_is_horizontally_centred() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40), spacing=10)
    group_left  = rects[0].x
    group_right = rects[-1].right
    group_center = (group_left + group_right) // 2
    assert abs(group_center - BOUNDS.centerx) <= 1


def test_row_zero_count_returns_empty() -> None:
    assert row(BOUNDS, count=0, item_size=(80, 40)) == []


def test_row_negative_count_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        row(BOUNDS, count=-1, item_size=(80, 40))


# ── column ────────────────────────────────────────────────────────────────────

def test_column_returns_correct_count() -> None:
    rects = column(BOUNDS, count=4, item_size=(120, 36))
    assert len(rects) == 4


def test_column_items_are_correct_size() -> None:
    rects = column(BOUNDS, count=4, item_size=(120, 36))
    for r in rects:
        assert r.width  == 120
        assert r.height == 36


def test_column_items_evenly_spaced() -> None:
    rects = column(BOUNDS, count=3, item_size=(120, 40), spacing=12)
    gap  = rects[1].y - rects[0].bottom
    gap2 = rects[2].y - rects[1].bottom
    assert gap  == 12
    assert gap2 == 12


def test_column_group_is_vertically_centred() -> None:
    rects = column(BOUNDS, count=3, item_size=(120, 40), spacing=10)
    group_top    = rects[0].y
    group_bottom = rects[-1].bottom
    group_center = (group_top + group_bottom) // 2
    assert abs(group_center - BOUNDS.centery) <= 1


def test_column_padding_shrinks_available_area() -> None:
    padded   = column(BOUNDS, count=1, item_size=(120, 40), padding=20)
    unpadded = column(BOUNDS, count=1, item_size=(120, 40), padding=0)
    # Centre should be the same (padding is symmetric)
    assert padded[0].centery == unpadded[0].centery


# ── grid ──────────────────────────────────────────────────────────────────────

def test_grid_returns_correct_count() -> None:
    rects = grid(BOUNDS, columns=3, count=7, item_size=(80, 60))
    assert len(rects) == 7


def test_grid_items_are_correct_size() -> None:
    rects = grid(BOUNDS, columns=3, count=6, item_size=(80, 60))
    for r in rects:
        assert r.width  == 80
        assert r.height == 60


def test_grid_fills_left_to_right_top_to_bottom() -> None:
    rects = grid(BOUNDS, columns=3, count=6, item_size=(80, 60), spacing=0)
    # First row: items 0, 1, 2 should have the same y
    assert rects[0].y == rects[1].y == rects[2].y
    # Second row: items 3, 4, 5 should have the same y, below first row
    assert rects[3].y == rects[4].y == rects[5].y
    assert rects[3].y > rects[0].y


def test_grid_spacing_applied() -> None:
    rects = grid(BOUNDS, columns=2, count=4, item_size=(80, 60), spacing=10)
    h_gap = rects[1].x - rects[0].right
    v_gap = rects[2].y - rects[0].bottom
    assert h_gap == 10
    assert v_gap == 10


def test_grid_zero_count_returns_empty() -> None:
    assert grid(BOUNDS, columns=3, count=0, item_size=(80, 60)) == []


def test_grid_invalid_columns_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        grid(BOUNDS, columns=0, count=4, item_size=(80, 60))
