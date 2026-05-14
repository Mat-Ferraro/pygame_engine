"""
tests/test_text_block.py

Tests for pygame_engine.ui.text.TextBlock.

Covers: text wrapping logic, dirty flag invalidation, property setters,
set_rect invalidation, invisible skip. Rendering output is not asserted
(visual) but render() is called to confirm it doesn't raise.
"""

import pygame
import pytest

from pygame_engine.graphics.text_utils import wrap_text
from pygame_engine.ui.text.text_block import TextBlock


RECT = pygame.Rect(0, 0, 300, 200)


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_text_is_empty() -> None:
    tb = TextBlock(RECT)
    assert tb.text == ""


def test_initial_text_stored() -> None:
    tb = TextBlock(RECT, "hello world")
    assert tb.text == "hello world"


def test_starts_dirty() -> None:
    tb = TextBlock(RECT, "hi")
    assert tb._dirty is True


# ── Property setters invalidate cache ─────────────────────────────────────────

def test_text_setter_marks_dirty() -> None:
    tb = TextBlock(RECT, "hello")
    tb._dirty = False
    tb.text = "world"
    assert tb._dirty is True


def test_text_setter_same_value_does_not_mark_dirty() -> None:
    tb = TextBlock(RECT, "same")
    tb._dirty = False
    tb.text = "same"
    assert tb._dirty is False


def test_align_setter_marks_dirty() -> None:
    tb = TextBlock(RECT, "hi", align="left")
    tb._dirty = False
    tb.align = "center"
    assert tb._dirty is True


def test_align_setter_same_value_does_not_mark_dirty() -> None:
    tb = TextBlock(RECT, "hi", align="left")
    tb._dirty = False
    tb.align = "left"
    assert tb._dirty is False


def test_padding_setter_marks_dirty() -> None:
    tb = TextBlock(RECT, "hi", padding=4)
    tb._dirty = False
    tb.padding = 8
    assert tb._dirty is True


def test_line_spacing_setter_marks_dirty() -> None:
    tb = TextBlock(RECT, "hi", line_spacing=4)
    tb._dirty = False
    tb.line_spacing = 8
    assert tb._dirty is True


def test_set_rect_marks_dirty() -> None:
    tb = TextBlock(RECT, "hi")
    tb._dirty = False
    tb.set_rect(pygame.Rect(10, 10, 200, 100))
    assert tb._dirty is True


# ── Text wrapping ─────────────────────────────────────────────────────────────

def _make_font() -> pygame.font.Font:
    return pygame.font.SysFont("arial", 16)


def test_wrap_empty_text_returns_single_empty_string() -> None:
    tb   = TextBlock(RECT)
    font = _make_font()
    result = wrap_text(font, "", 300)
    assert result == [""]


def test_wrap_short_text_fits_on_one_line() -> None:
    tb   = TextBlock(RECT)
    font = _make_font()
    result = wrap_text(font, "Hi", 300)
    assert len(result) == 1
    assert result[0] == "Hi"


def test_wrap_long_text_splits_across_lines() -> None:
    tb   = TextBlock(RECT)
    font = _make_font()
    long_text = "word " * 30  # will definitely overflow 100px
    result = wrap_text(font, long_text.strip(), 100)
    assert len(result) > 1


def test_wrap_preserves_newlines_as_paragraph_breaks() -> None:
    tb   = TextBlock(RECT)
    font = _make_font()
    result = wrap_text(font, "line one\nline two", 300)
    assert len(result) == 2
    assert result[0] == "line one"
    assert result[1] == "line two"


def test_wrap_empty_paragraph_adds_empty_string() -> None:
    tb   = TextBlock(RECT)
    font = _make_font()
    result = wrap_text(font, "before\n\nafter", 300)
    # Should have: "before", "", "after"
    assert "" in result
    assert "before" in result
    assert "after" in result


# ── Rendering ─────────────────────────────────────────────────────────────────

def test_render_does_not_raise(display_surface) -> None:
    tb = TextBlock(RECT, "Hello, world!")
    tb.render(display_surface)


def test_render_clears_dirty_flag(display_surface) -> None:
    tb = TextBlock(RECT, "hello")
    assert tb._dirty is True
    tb.render(display_surface)
    assert tb._dirty is False


def test_render_creates_cache_surface(display_surface) -> None:
    tb = TextBlock(RECT, "hello")
    assert tb._cache_surface is None
    tb.render(display_surface)
    assert tb._cache_surface is not None


def test_render_skips_when_invisible(display_surface) -> None:
    tb = TextBlock(RECT, "hello")
    tb.visible = False
    tb.render(display_surface)
    assert tb._cache_surface is None   # never built


def test_second_render_reuses_cache(display_surface) -> None:
    tb = TextBlock(RECT, "hello")
    tb.render(display_surface)
    first_surf = tb._cache_surface
    tb.render(display_surface)
    assert tb._cache_surface is first_surf   # same object


def test_text_change_forces_cache_rebuild(display_surface) -> None:
    tb = TextBlock(RECT, "hello")
    tb.render(display_surface)
    first_surf = tb._cache_surface
    tb.text = "world"
    tb.render(display_surface)
    assert tb._cache_surface is not first_surf
