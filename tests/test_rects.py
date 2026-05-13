"""
tests/test_rects.py

Tests for pygame_engine.utils.rects.

Covers: construction helpers, inset, snap, clamp_inside, split helpers.
"""

import pygame
import pytest

from pygame_engine.utils.rects import (
    clamp_inside,
    inset,
    inset_xy,
    rect_from_center,
    rect_from_corners,
    snap_to_grid,
    split_horizontal,
    split_vertical,
)


# ── Construction ──────────────────────────────────────────────────────────────

def test_rect_from_center() -> None:
    r = rect_from_center((200, 150), (100, 60))
    assert r.centerx == 200
    assert r.centery == 150
    assert r.width   == 100
    assert r.height  == 60


def test_rect_from_center_at_origin() -> None:
    r = rect_from_center((0, 0), (50, 30))
    assert r.centerx == 0
    assert r.centery == 0


def test_rect_from_corners() -> None:
    r = rect_from_corners((10, 20), (110, 80))
    assert r.x      == 10
    assert r.y      == 20
    assert r.width  == 100
    assert r.height == 60


def test_rect_from_corners_same_point_zero_size() -> None:
    r = rect_from_corners((50, 50), (50, 50))
    assert r.width  == 0
    assert r.height == 0


# ── Inset ─────────────────────────────────────────────────────────────────────

def test_inset_shrinks_all_sides_equally() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    i = inset(r, 10)
    assert i.x      == 10
    assert i.y      == 10
    assert i.width  == 180
    assert i.height == 80


def test_inset_zero_leaves_rect_unchanged() -> None:
    r = pygame.Rect(10, 20, 200, 100)
    assert inset(r, 0) == r


def test_inset_preserves_center() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    i = inset(r, 20)
    assert i.centerx == r.centerx
    assert i.centery == r.centery


def test_inset_xy_shrinks_independently() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    i = inset_xy(r, 20, 5)
    assert i.width  == 160
    assert i.height == 90


def test_inset_xy_zero_x_only_shrinks_height() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    i = inset_xy(r, 0, 10)
    assert i.width  == 200
    assert i.height == 80


def test_inset_xy_zero_y_only_shrinks_width() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    i = inset_xy(r, 15, 0)
    assert i.width  == 170
    assert i.height == 100


# ── Snapping ──────────────────────────────────────────────────────────────────

def test_snap_to_grid_rounds_to_nearest_cell() -> None:
    r = pygame.Rect(13, 27, 100, 50)
    s = snap_to_grid(r, 10)
    assert s.x == 10
    assert s.y == 30


def test_snap_to_grid_preserves_size() -> None:
    r = pygame.Rect(13, 27, 100, 50)
    s = snap_to_grid(r, 10)
    assert s.width  == 100
    assert s.height == 50


def test_snap_to_grid_already_aligned() -> None:
    r = pygame.Rect(20, 40, 80, 60)
    s = snap_to_grid(r, 10)
    assert s.x == 20
    assert s.y == 40


def test_snap_to_grid_rounds_up() -> None:
    r = pygame.Rect(16, 0, 10, 10)
    s = snap_to_grid(r, 10)
    assert s.x == 20   # 16 rounds to 20


def test_snap_to_grid_origin() -> None:
    r = pygame.Rect(0, 0, 50, 50)
    s = snap_to_grid(r, 16)
    assert s.x == 0
    assert s.y == 0


# ── Clamping ──────────────────────────────────────────────────────────────────

def test_clamp_inside_moves_rect_fully_inside() -> None:
    outer   = pygame.Rect(0, 0, 400, 300)
    inner   = pygame.Rect(350, 250, 100, 80)
    clamped = clamp_inside(inner, outer)
    assert clamped.right  <= outer.right
    assert clamped.bottom <= outer.bottom
    assert clamped.left   >= outer.left
    assert clamped.top    >= outer.top


def test_clamp_inside_does_not_move_rect_already_inside() -> None:
    outer   = pygame.Rect(0, 0, 400, 300)
    inner   = pygame.Rect(10, 10, 50, 50)
    clamped = clamp_inside(inner, outer)
    assert clamped == inner


def test_clamp_inside_preserves_size() -> None:
    outer   = pygame.Rect(0, 0, 400, 300)
    inner   = pygame.Rect(380, 280, 100, 80)
    clamped = clamp_inside(inner, outer)
    assert clamped.width  == inner.width
    assert clamped.height == inner.height


def test_clamp_inside_top_left_overhang() -> None:
    outer   = pygame.Rect(50, 50, 300, 200)
    inner   = pygame.Rect(0, 0, 60, 40)
    clamped = clamp_inside(inner, outer)
    assert clamped.left >= outer.left
    assert clamped.top  >= outer.top


def test_clamp_inside_centred_rect_unchanged() -> None:
    outer   = pygame.Rect(0, 0, 400, 300)
    inner   = pygame.Rect(150, 100, 100, 100)
    clamped = clamp_inside(inner, outer)
    assert clamped == inner


# ── Splitting ─────────────────────────────────────────────────────────────────

def test_split_horizontal_correct_widths() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    left, right = split_horizontal(r, 0.25)
    assert left.width  == 50
    assert right.width == 150


def test_split_horizontal_halves() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    left, right = split_horizontal(r, 0.5)
    assert left.width  == 100
    assert right.width == 100


def test_split_horizontal_left_right_adjacent() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    left, right = split_horizontal(r, 0.4)
    assert left.right == right.left


def test_split_horizontal_preserves_height() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    left, right = split_horizontal(r, 0.5)
    assert left.height  == 100
    assert right.height == 100


def test_split_horizontal_at_offset_position() -> None:
    r = pygame.Rect(50, 30, 200, 100)
    left, right = split_horizontal(r, 0.5)
    assert left.x  == 50
    assert right.x == 150


def test_split_vertical_correct_heights() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    top, bottom = split_vertical(r, 0.4)
    assert top.height    == 40
    assert bottom.height == 60


def test_split_vertical_halves() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    top, bottom = split_vertical(r, 0.5)
    assert top.height    == 50
    assert bottom.height == 50


def test_split_vertical_top_bottom_adjacent() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    top, bottom = split_vertical(r, 0.3)
    assert top.bottom == bottom.top


def test_split_vertical_preserves_width() -> None:
    r = pygame.Rect(0, 0, 200, 100)
    top, bottom = split_vertical(r, 0.5)
    assert top.width    == 200
    assert bottom.width == 200


def test_split_vertical_at_offset_position() -> None:
    r = pygame.Rect(20, 40, 200, 100)
    top, bottom = split_vertical(r, 0.5)
    assert top.y    == 40
    assert bottom.y == 90
