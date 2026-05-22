"""
Tests for pygame_engine.ui.controls.ProgressBar.
"""

import pygame
import pytest

from pygame_engine.ui.controls.progress_bar import ProgressBar



# ── CHANGE-02: RenderContext helper ──────────────────────────────────────────

def _ctx():
    """Return a default RenderContext for render() calls in tests."""
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    return RenderContext(theme=get_theme())

RECT = pygame.Rect(0, 0, 200, 20)


def test_default_value_is_one() -> None:
    bar = ProgressBar(RECT)
    assert bar.value == 1.0


def test_value_clamped_above_one() -> None:
    bar = ProgressBar(RECT, value=1.5)
    assert bar.value == 1.0


def test_value_clamped_below_zero() -> None:
    bar = ProgressBar(RECT, value=-0.5)
    assert bar.value == 0.0


def test_value_setter_clamps() -> None:
    bar = ProgressBar(RECT)
    bar.value = 2.0
    assert bar.value == 1.0
    bar.value = -1.0
    assert bar.value == 0.0


def test_value_midpoint() -> None:
    bar = ProgressBar(RECT, value=0.5)
    assert bar.value == 0.5


def test_horizontal_fill_rect_width() -> None:
    bar = ProgressBar(RECT, value=0.5, direction="horizontal")
    fill = bar._compute_fill_rect()
    assert fill.width  == 100   # 50% of 200
    assert fill.height == 20
    assert fill.x      == RECT.x
    assert fill.y      == RECT.y


def test_horizontal_full_fill_rect() -> None:
    bar = ProgressBar(RECT, value=1.0)
    fill = bar._compute_fill_rect()
    assert fill.width == 200


def test_horizontal_empty_fill_rect() -> None:
    bar = ProgressBar(RECT, value=0.0)
    fill = bar._compute_fill_rect()
    assert fill.width == 0


def test_vertical_fill_rect_height() -> None:
    rect = pygame.Rect(0, 0, 20, 100)
    bar  = ProgressBar(rect, value=0.4, direction="vertical")
    fill = bar._compute_fill_rect()
    assert fill.height == 40    # 40% of 100
    assert fill.width  == 20
    assert fill.bottom == rect.bottom


def test_vertical_full_fill_rect() -> None:
    rect = pygame.Rect(0, 0, 20, 100)
    bar  = ProgressBar(rect, value=1.0, direction="vertical")
    fill = bar._compute_fill_rect()
    assert fill.height == 100
    assert fill.y == rect.y


def test_vertical_empty_fill_rect() -> None:
    rect = pygame.Rect(0, 0, 20, 100)
    bar  = ProgressBar(rect, value=0.0, direction="vertical")
    fill = bar._compute_fill_rect()
    assert fill.height == 0


def test_invisible_bar_skips_render(display_surface) -> None:
    bar = ProgressBar(RECT, value=0.5)
    bar.visible = False
    # Should not raise
    bar.render(display_surface, _ctx())


def test_direction_property() -> None:
    bar = ProgressBar(RECT, direction="vertical")
    assert bar.direction == "vertical"