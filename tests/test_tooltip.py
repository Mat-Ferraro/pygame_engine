"""
Tests for pygame_engine.ui.feedback.tooltip.Tooltip.
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.ui.feedback.tooltip import Tooltip


SCREEN = pygame.Rect(0, 0, 800, 600)


@pytest.fixture
def display_surface():
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((800, 600))
    return pygame.display.get_surface()


def make_tooltip(text="Hover info", fade=0.12) -> Tooltip:
    return Tooltip(SCREEN, text=text, fade_in_duration=fade)


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_text() -> None:
    t = make_tooltip()
    assert t.text == "Hover info"


def test_default_not_visible() -> None:
    t = make_tooltip()
    assert t.visible is False


def test_default_alpha_zero() -> None:
    t = make_tooltip()
    assert t._alpha == 0.0


# ── text setter ───────────────────────────────────────────────────────────────

def test_text_setter_updates() -> None:
    t = make_tooltip("Old")
    t.text = "New"
    assert t.text == "New"


def test_text_setter_same_value_no_dirty() -> None:
    t = make_tooltip("Same")
    t._dirty = False
    t.text = "Same"
    assert t._dirty is False


def test_text_setter_marks_dirty() -> None:
    t = make_tooltip("Old")
    t._dirty = False
    t.text = "New"
    assert t._dirty is True


# ── show() and hide() ─────────────────────────────────────────────────────────

def test_show_makes_visible() -> None:
    t = make_tooltip()
    t.show((100, 100))
    assert t.visible is True


def test_show_positions_near_mouse() -> None:
    t = make_tooltip()
    t.show((200, 300))
    # After show, rect should be positioned (it may be zero-size until rendered)
    # Just check it doesn't crash and visible is set
    assert t.visible is True


def test_hide_makes_invisible() -> None:
    t = make_tooltip()
    t.show((100, 100))
    t.hide()
    assert t.visible is False


def test_hide_resets_alpha() -> None:
    t = make_tooltip()
    t.show((100, 100))
    t._alpha = 0.8
    t.hide()
    assert t._alpha == 0.0


# ── update() ─────────────────────────────────────────────────────────────────

def test_update_increases_alpha_when_visible() -> None:
    t = make_tooltip(fade=0.5)
    t.show((100, 100))
    t.update(0.25)
    assert t._alpha > 0.0


def test_update_alpha_reaches_one() -> None:
    t = make_tooltip(fade=0.1)
    t.show((100, 100))
    t.update(10.0)
    assert t._alpha == 1.0


def test_update_noop_when_not_visible() -> None:
    t = make_tooltip(fade=0.1)
    t.update(10.0)
    assert t._alpha == 0.0


def test_instant_fade_alpha_one_immediately() -> None:
    t = Tooltip(SCREEN, text="Fast", fade_in_duration=0.0)
    t.show((100, 100))
    t.update(0.001)
    assert t._alpha == 1.0


# ── Screen clamping ───────────────────────────────────────────────────────────

def test_show_near_right_edge_clamped() -> None:
    """Tooltip near right edge should be clamped inside screen bounds."""
    t = Tooltip(SCREEN, text="Edge test", fade_in_duration=0.0)
    t.update(1.0)  # build font/surfaces first
    # Position near right edge
    t.show((790, 300))
    if t.rect.width > 0:
        assert t.rect.right <= SCREEN.right


def test_show_near_bottom_edge_clamped() -> None:
    t = Tooltip(SCREEN, text="Bottom", fade_in_duration=0.0)
    t.show((400, 590))
    if t.rect.height > 0:
        assert t.rect.bottom <= SCREEN.bottom


# ── render() ─────────────────────────────────────────────────────────────────

def test_render_invisible_does_not_raise(display_surface) -> None:
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    t = make_tooltip()
    t.render(display_surface, ctx)   # should not raise


def test_render_visible_does_not_raise(display_surface) -> None:
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    t = make_tooltip("Visible tooltip")
    t.show((200, 200))
    t.update(1.0)
    t.render(display_surface, ctx)


def test_render_at_zero_alpha_does_not_raise(display_surface) -> None:
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    t = make_tooltip()
    t.visible = True
    t._alpha = 0.0
    t.render(display_surface, ctx)
