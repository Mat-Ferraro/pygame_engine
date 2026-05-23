"""
Tests for pygame_engine.ui.feedback.toast.Toast.

Uses a display_surface fixture so render() can actually draw.
Timer internals are driven directly via update(dt) calls.

Note: Toast.update() advances ONE phase per call. To traverse multiple
phases, call update() once per phase transition.
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.ui.feedback.toast import Toast, _PHASE_IDLE, _PHASE_FADE_IN, _PHASE_HOLD, _PHASE_FADE_OUT, _PHASE_EXPIRED


RECT = pygame.Rect(100, 600, 300, 48)

# Small epsilon to push past a phase boundary
_E = 0.001


@pytest.fixture
def display_surface():
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((800, 600))
    return pygame.display.get_surface()


def make_toast(text="Saved!", duration=2.0, kind="info") -> Toast:
    t = Toast(text, duration=duration, kind=kind)
    t.set_rect(RECT)
    return t


def advance_to_expired(t: Toast) -> None:
    """Drive a toast through its full lifecycle (three update calls)."""
    t.update(Toast.FADE_IN_DURATION + _E)   # FADE_IN -> HOLD
    t.update(t._duration + _E)              # HOLD -> FADE_OUT
    t.update(Toast.FADE_OUT_DURATION + _E)  # FADE_OUT -> EXPIRED


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_text() -> None:
    t = Toast()
    assert t.text == ""


def test_custom_text() -> None:
    t = Toast("Hello")
    assert t.text == "Hello"


def test_default_not_visible() -> None:
    t = Toast("msg")
    assert t.visible is False


def test_default_phase_idle() -> None:
    t = Toast("msg")
    assert t._phase == _PHASE_IDLE


def test_not_active_before_show() -> None:
    t = Toast("msg")
    assert t.is_active is False


def test_not_expired_before_show() -> None:
    t = Toast("msg")
    assert t.is_expired is False


# ── show() ────────────────────────────────────────────────────────────────────

def test_show_makes_visible() -> None:
    t = make_toast()
    t.show()
    assert t.visible is True


def test_show_enters_fade_in_phase() -> None:
    t = make_toast()
    t.show()
    assert t._phase == _PHASE_FADE_IN


def test_show_marks_active() -> None:
    t = make_toast()
    t.show()
    assert t.is_active is True


def test_show_can_be_called_again_to_restart() -> None:
    """show() after expiry resets the lifecycle."""
    t = make_toast(duration=0.1)
    t.show()
    advance_to_expired(t)
    assert t.is_expired
    t.show()   # restart
    assert t._phase == _PHASE_FADE_IN
    assert t.is_active is True


# ── text setter ───────────────────────────────────────────────────────────────

def test_text_setter_changes_text() -> None:
    t = make_toast("Before")
    t.text = "After"
    assert t.text == "After"


def test_text_setter_same_value_no_dirty() -> None:
    t = make_toast("Same")
    t._dirty = False
    t.text = "Same"
    assert t._dirty is False


def test_text_setter_different_value_marks_dirty() -> None:
    t = make_toast("Old")
    t._dirty = False
    t.text = "New"
    assert t._dirty is True


# ── Lifecycle / phase transitions ─────────────────────────────────────────────

def test_update_advances_alpha_during_fade_in() -> None:
    t = make_toast()
    t.show()
    t.update(Toast.FADE_IN_DURATION * 0.5)
    assert 0.0 < t._alpha < 1.0


def test_update_alpha_one_at_end_of_fade_in() -> None:
    """After fade-in completes one update(), the phase moves to HOLD."""
    t = make_toast(duration=0.5)
    t.show()
    t.update(Toast.FADE_IN_DURATION + _E)
    assert t._phase == _PHASE_HOLD


def test_hold_phase_alpha_is_one() -> None:
    t = make_toast(duration=0.5)
    t.show()
    t.update(Toast.FADE_IN_DURATION + _E)   # -> HOLD
    t.update(0.01)                           # advance inside HOLD
    assert abs(t._alpha - 1.0) < 1e-6


def test_transitions_to_fade_out_after_hold() -> None:
    """Two update() calls: FADE_IN done, then HOLD done."""
    t = make_toast(duration=0.1)
    t.show()
    t.update(Toast.FADE_IN_DURATION + _E)   # -> HOLD
    t.update(0.1 + _E)                      # -> FADE_OUT
    assert t._phase == _PHASE_FADE_OUT


def test_expires_after_full_lifecycle() -> None:
    """Three update() calls drive toast to expired."""
    t = make_toast(duration=0.1)
    t.show()
    advance_to_expired(t)
    assert t.is_expired is True
    assert t.visible is False


def test_alpha_zero_when_expired() -> None:
    t = make_toast(duration=0.1)
    t.show()
    advance_to_expired(t)
    assert t._alpha == 0.0


# ── dismiss() ─────────────────────────────────────────────────────────────────

def test_dismiss_during_hold_enters_fade_out() -> None:
    t = make_toast(duration=10.0)
    t.show()
    t.update(Toast.FADE_IN_DURATION + _E)   # -> HOLD
    t.update(0.01)                           # still in HOLD
    assert t._phase == _PHASE_HOLD
    t.dismiss()
    assert t._phase == _PHASE_FADE_OUT


def test_dismiss_during_fade_in_enters_fade_out() -> None:
    t = make_toast()
    t.show()
    t.update(0.01)   # still fading in
    t.dismiss()
    assert t._phase == _PHASE_FADE_OUT


def test_dismiss_when_idle_does_nothing() -> None:
    t = make_toast()
    t.dismiss()   # should not raise
    assert t._phase == _PHASE_IDLE


# ── render ────────────────────────────────────────────────────────────────────

def test_render_when_invisible_does_not_raise(display_surface) -> None:
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    t = make_toast()
    t.visible = False
    t.render(display_surface, ctx)


def test_render_when_active_does_not_raise(display_surface) -> None:
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    t = make_toast("Test render")
    t.set_rect(pygame.Rect(10, 10, 200, 48))
    t.show()
    t.update(Toast.FADE_IN_DURATION + _E)   # -> HOLD
    t.render(display_surface, ctx)


def test_render_kinds_do_not_raise(display_surface) -> None:
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme
    ctx = RenderContext(theme=get_theme())
    for kind in ("info", "success", "warning", "error"):
        t = Toast("msg", kind=kind)
        t.set_rect(pygame.Rect(10, 10, 200, 48))
        t.show()
        t.update(Toast.FADE_IN_DURATION + _E)
        t.render(display_surface, ctx)


# ── update noop when idle or expired ─────────────────────────────────────────

def test_update_noop_when_idle() -> None:
    t = make_toast()
    t.update(1.0)   # should not raise, phase stays idle
    assert t._phase == _PHASE_IDLE


def test_update_noop_when_expired() -> None:
    """After expiry, further update() calls are no-ops."""
    t = make_toast(duration=0.1)
    t.show()
    advance_to_expired(t)
    assert t.is_expired
    t.update(1.0)   # should not raise
    assert t.is_expired
