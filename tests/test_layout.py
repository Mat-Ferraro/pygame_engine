"""
tests/test_layout.py

Tests for pygame_engine.layout — anchor, row, column, grid.

Covers: correct rect positions, spacing, padding, alignment, edge cases.
"""

import pygame
import pytest

from pygame_engine.layout import anchor, column, grid, row


BOUNDS = pygame.Rect(0, 0, 600, 400)


# ── anchor ────────────────────────────────────────────────────────────────────

def test_anchor_center() -> None:
    r = anchor(BOUNDS, (100, 50), "center")
    assert r.centerx == BOUNDS.centerx
    assert r.centery == BOUNDS.centery
    assert r.width   == 100
    assert r.height  == 50


def test_anchor_top_left() -> None:
    r = anchor(BOUNDS, (80, 40), "top_left")
    assert r.x == 0
    assert r.y == 0


def test_anchor_top_left_with_margin() -> None:
    r = anchor(BOUNDS, (80, 40), "top_left", margin=10)
    assert r.x == 10
    assert r.y == 10


def test_anchor_top_right() -> None:
    r = anchor(BOUNDS, (80, 40), "top_right")
    assert r.right == BOUNDS.right
    assert r.y     == 0


def test_anchor_bottom_left() -> None:
    r = anchor(BOUNDS, (80, 40), "bottom_left")
    assert r.x      == 0
    assert r.bottom == BOUNDS.bottom


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


def test_anchor_left_center() -> None:
    r = anchor(BOUNDS, (60, 40), "left", margin=8)
    assert r.x       == 8
    assert r.centery == BOUNDS.centery


def test_anchor_right_center() -> None:
    r = anchor(BOUNDS, (60, 40), "right", margin=8)
    assert r.right   == BOUNDS.right - 8
    assert r.centery == BOUNDS.centery


def test_anchor_offset_applied() -> None:
    r = anchor(BOUNDS, (100, 50), "center", offset=(10, -20))
    assert r.centerx == BOUNDS.centerx + 10
    assert r.centery == BOUNDS.centery - 20


def test_anchor_offset_with_top_left() -> None:
    r = anchor(BOUNDS, (80, 40), "top_left", margin=5, offset=(3, 2))
    assert r.x == 8
    assert r.y == 7


def test_anchor_invalid_point_raises() -> None:
    with pytest.raises(ValueError):
        anchor(BOUNDS, (100, 50), "invalid_point")


def test_anchor_preserves_size() -> None:
    for point in ("top_left", "top", "top_right", "left", "center",
                  "right", "bottom_left", "bottom", "bottom_right"):
        r = anchor(BOUNDS, (120, 60), point)
        assert r.width  == 120
        assert r.height == 60


def test_anchor_on_offset_bounds() -> None:
    bounds = pygame.Rect(100, 50, 400, 300)
    r = anchor(bounds, (100, 50), "center")
    assert r.centerx == bounds.centerx
    assert r.centery == bounds.centery


# ── row ───────────────────────────────────────────────────────────────────────

def test_row_returns_correct_count() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40))
    assert len(rects) == 3


def test_row_items_are_correct_size() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40))
    for r in rects:
        assert r.width  == 80
        assert r.height == 40


def test_row_items_left_to_right() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40), spacing=0)
    assert rects[0].x < rects[1].x < rects[2].x


def test_row_items_evenly_spaced() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40), spacing=10)
    gap1 = rects[1].x - rects[0].right
    gap2 = rects[2].x - rects[1].right
    assert gap1 == 10
    assert gap2 == 10


def test_row_group_is_horizontally_centred() -> None:
    rects = row(BOUNDS, count=3, item_size=(80, 40), spacing=10)
    group_left   = rects[0].x
    group_right  = rects[-1].right
    group_center = (group_left + group_right) // 2
    assert abs(group_center - BOUNDS.centerx) <= 1


def test_row_align_start() -> None:
    rects = row(BOUNDS, count=2, item_size=(80, 40), align="start")
    assert rects[0].y == BOUNDS.y


def test_row_align_end() -> None:
    rects = row(BOUNDS, count=2, item_size=(80, 40), align="end")
    assert rects[0].bottom == BOUNDS.bottom


def test_row_align_center() -> None:
    rects = row(BOUNDS, count=2, item_size=(80, 40), align="center")
    for r in rects:
        assert r.centery == BOUNDS.centery


def test_row_with_padding() -> None:
    padded   = row(BOUNDS, count=1, item_size=(80, 40), padding=30)
    unpadded = row(BOUNDS, count=1, item_size=(80, 40), padding=0)
    assert padded[0].centerx == unpadded[0].centerx


def test_row_zero_count_returns_empty() -> None:
    assert row(BOUNDS, count=0, item_size=(80, 40)) == []


def test_row_negative_count_raises() -> None:
    with pytest.raises(ValueError):
        row(BOUNDS, count=-1, item_size=(80, 40))


def test_row_single_item_centred() -> None:
    rects = row(BOUNDS, count=1, item_size=(100, 40))
    assert rects[0].centerx == BOUNDS.centerx


# ── column ────────────────────────────────────────────────────────────────────

def test_column_returns_correct_count() -> None:
    rects = column(BOUNDS, count=4, item_size=(120, 36))
    assert len(rects) == 4


def test_column_items_are_correct_size() -> None:
    rects = column(BOUNDS, count=4, item_size=(120, 36))
    for r in rects:
        assert r.width  == 120
        assert r.height == 36


def test_column_items_top_to_bottom() -> None:
    rects = column(BOUNDS, count=3, item_size=(120, 40), spacing=0)
    assert rects[0].y < rects[1].y < rects[2].y


def test_column_items_evenly_spaced() -> None:
    rects = column(BOUNDS, count=3, item_size=(120, 40), spacing=12)
    gap1 = rects[1].y - rects[0].bottom
    gap2 = rects[2].y - rects[1].bottom
    assert gap1 == 12
    assert gap2 == 12


def test_column_group_is_vertically_centred() -> None:
    rects = column(BOUNDS, count=3, item_size=(120, 40), spacing=10)
    group_top    = rects[0].y
    group_bottom = rects[-1].bottom
    group_center = (group_top + group_bottom) // 2
    assert abs(group_center - BOUNDS.centery) <= 1


def test_column_align_start() -> None:
    rects = column(BOUNDS, count=2, item_size=(120, 40), align="start")
    assert rects[0].x == BOUNDS.x


def test_column_align_end() -> None:
    rects = column(BOUNDS, count=2, item_size=(120, 40), align="end")
    assert rects[0].right == BOUNDS.right


def test_column_align_center() -> None:
    rects = column(BOUNDS, count=2, item_size=(120, 40), align="center")
    for r in rects:
        assert r.centerx == BOUNDS.centerx


def test_column_zero_count_returns_empty() -> None:
    assert column(BOUNDS, count=0, item_size=(120, 40)) == []


def test_column_negative_count_raises() -> None:
    with pytest.raises(ValueError):
        column(BOUNDS, count=-1, item_size=(120, 40))


def test_column_single_item_centred() -> None:
    rects = column(BOUNDS, count=1, item_size=(120, 40))
    assert rects[0].centery == BOUNDS.centery


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
    assert rects[0].y == rects[1].y == rects[2].y
    assert rects[3].y == rects[4].y == rects[5].y
    assert rects[3].y > rects[0].y


def test_grid_spacing_applied() -> None:
    rects = grid(BOUNDS, columns=2, count=4, item_size=(80, 60), spacing=10)
    h_gap = rects[1].x - rects[0].right
    v_gap = rects[2].y - rects[0].bottom
    assert h_gap == 10
    assert v_gap == 10


def test_grid_partial_last_row() -> None:
    rects = grid(BOUNDS, columns=3, count=4, item_size=(80, 60))
    assert len(rects) == 4


def test_grid_single_column() -> None:
    rects = grid(BOUNDS, columns=1, count=3, item_size=(100, 40), spacing=5)
    assert len(rects) == 3
    for r in rects:
        assert r.width == 100


def test_grid_zero_count_returns_empty() -> None:
    assert grid(BOUNDS, columns=3, count=0, item_size=(80, 60)) == []


def test_grid_invalid_columns_raises() -> None:
    with pytest.raises(ValueError):
        grid(BOUNDS, columns=0, count=4, item_size=(80, 60))


def test_grid_group_centred_in_bounds() -> None:
    rects = grid(BOUNDS, columns=2, count=4, item_size=(80, 60), spacing=0)
    group_left   = min(r.x for r in rects)
    group_right  = max(r.right for r in rects)
    group_center = (group_left + group_right) // 2
    assert abs(group_center - BOUNDS.centerx) <= 1
