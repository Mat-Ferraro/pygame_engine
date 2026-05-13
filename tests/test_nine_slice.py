"""
tests/test_nine_slice.py

Tests for pygame_engine.graphics.nine_slice.

Covers: border normalisation, draw_nine_slice geometry, error cases,
make_nine_slice_surface output size, NineSlicePanel caching.
"""

import pygame
import pytest

from pygame_engine.graphics.nine_slice import (
    NineSlicePanel,
    _normalise_border,
    draw_nine_slice,
    make_nine_slice_surface,
)


def make_source(w: int = 32, h: int = 32) -> pygame.Surface:
    """Create a solid-colour source surface for testing."""
    s = pygame.Surface((w, h))
    s.fill((100, 150, 200))
    return s


# ── Border normalisation ──────────────────────────────────────────────────────

def test_normalise_int_expands_to_four() -> None:
    assert _normalise_border(8) == (8, 8, 8, 8)


def test_normalise_tuple_passthrough() -> None:
    assert _normalise_border((4, 6, 4, 6)) == (4, 6, 4, 6)


def test_normalise_invalid_raises() -> None:
    with pytest.raises(ValueError):
        _normalise_border((1, 2))  # type: ignore[arg-type]


# ── draw_nine_slice ───────────────────────────────────────────────────────────

def test_draw_same_size_as_source_does_not_raise(display_surface) -> None:
    source = make_source(32, 32)
    rect   = pygame.Rect(0, 0, 32, 32)
    draw_nine_slice(display_surface, source, rect, border=8)


def test_draw_larger_than_source_does_not_raise(display_surface) -> None:
    source = make_source(32, 32)
    rect   = pygame.Rect(0, 0, 200, 120)
    draw_nine_slice(display_surface, source, rect, border=8)


def test_draw_with_tuple_border_does_not_raise(display_surface) -> None:
    source = make_source(32, 32)
    rect   = pygame.Rect(0, 0, 200, 120)
    draw_nine_slice(display_surface, source, rect, border=(8, 10, 8, 10))


def test_draw_destination_too_small_raises(display_surface) -> None:
    source = make_source(32, 32)
    rect   = pygame.Rect(0, 0, 10, 10)   # smaller than border*2
    with pytest.raises(ValueError):
        draw_nine_slice(display_surface, source, rect, border=8)


def test_draw_at_offset_position_does_not_raise(display_surface) -> None:
    source = make_source(32, 32)
    rect   = pygame.Rect(50, 50, 200, 150)
    draw_nine_slice(display_surface, source, rect, border=8)


# ── make_nine_slice_surface ───────────────────────────────────────────────────

def test_output_surface_has_correct_size() -> None:
    source = make_source(32, 32)
    out    = make_nine_slice_surface(source, (200, 120), border=8)
    assert out.get_size() == (200, 120)


def test_output_surface_exact_source_size() -> None:
    source = make_source(32, 32)
    out    = make_nine_slice_surface(source, (32, 32), border=8)
    assert out.get_size() == (32, 32)


def test_output_surface_large() -> None:
    source = make_source(32, 32)
    out    = make_nine_slice_surface(source, (800, 600), border=8)
    assert out.get_size() == (800, 600)


def test_output_preserves_srcalpha_flag() -> None:
    source = pygame.Surface((32, 32), pygame.SRCALPHA)
    source.fill((100, 150, 200, 200))
    out = make_nine_slice_surface(source, (100, 80), border=8)
    assert out.get_flags() & pygame.SRCALPHA


# ── NineSlicePanel ────────────────────────────────────────────────────────────

def test_panel_renders_without_raising(display_surface) -> None:
    source = make_source(32, 32)
    panel  = NineSlicePanel(pygame.Rect(0, 0, 200, 120), source, border=8)
    panel.render(display_surface)


def test_panel_invisible_skips_render(display_surface) -> None:
    source = make_source(32, 32)
    panel  = NineSlicePanel(pygame.Rect(0, 0, 200, 120), source, border=8)
    panel.visible = False
    panel.render(display_surface)
    assert panel._cached is None   # never built


def test_panel_builds_cache_on_first_render(display_surface) -> None:
    source = make_source(32, 32)
    panel  = NineSlicePanel(pygame.Rect(0, 0, 200, 120), source, border=8)
    assert panel._cached is None
    panel.render(display_surface)
    assert panel._cached is not None


def test_panel_reuses_cache_on_second_render(display_surface) -> None:
    source = make_source(32, 32)
    panel  = NineSlicePanel(pygame.Rect(0, 0, 200, 120), source, border=8)
    panel.render(display_surface)
    first_cache = panel._cached
    panel.render(display_surface)
    assert panel._cached is first_cache


def test_panel_rebuilds_cache_on_resize(display_surface) -> None:
    source = make_source(32, 32)
    panel  = NineSlicePanel(pygame.Rect(0, 0, 200, 120), source, border=8)
    panel.render(display_surface)
    first_cache = panel._cached
    panel.set_rect(pygame.Rect(0, 0, 300, 200))
    panel.render(display_surface)
    assert panel._cached is not first_cache


def test_panel_cached_surface_matches_rect_size(display_surface) -> None:
    source = make_source(32, 32)
    rect   = pygame.Rect(0, 0, 256, 128)
    panel  = NineSlicePanel(rect, source, border=8)
    panel.render(display_surface)
    assert panel._cached is not None
    assert panel._cached.get_size() == (256, 128)
