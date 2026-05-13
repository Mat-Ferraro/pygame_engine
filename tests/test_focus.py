"""
tests/test_focus.py

Tests for pygame_engine.ui.focus.FocusManager.

Covers: focusable child filtering, Tab/Shift+Tab traversal, focus_first,
focus_none, keyboard routing to focused child, wrapping behaviour.
"""

import pygame
import pytest

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.containers.panel import Panel
from pygame_engine.ui.containers.stack import Stack
from pygame_engine.ui.focus import FocusManager


RECT = pygame.Rect(0, 0, 400, 300)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_focusable(rect=None) -> Widget:
    w = Widget(rect or pygame.Rect(0, 0, 100, 40))
    w.focusable = True
    return w


def make_display(rect=None) -> Widget:
    w = Widget(rect or pygame.Rect(0, 0, 100, 20))
    w.focusable = False
    return w


def tab_event(shift: bool = False) -> pygame.event.Event:
    mod = pygame.KMOD_SHIFT if shift else 0
    return pygame.event.Event(pygame.KEYDOWN, {
        "key": pygame.K_TAB, "mod": mod,
        "unicode": "\t", "scancode": 0,
    })


# ── FocusManager._focusable_children ─────────────────────────────────────────

def test_focusable_children_filters_non_focusable() -> None:
    fm = FocusManager()
    children = [make_focusable(), make_display(), make_focusable()]
    result = fm._focusable_children(children)
    assert len(result) == 2


def test_focusable_children_excludes_invisible() -> None:
    fm = FocusManager()
    w = make_focusable()
    w.visible = False
    result = fm._focusable_children([w])
    assert result == []


def test_focusable_children_excludes_disabled() -> None:
    fm = FocusManager()
    w = make_focusable()
    w.enabled = False
    result = fm._focusable_children([w])
    assert result == []


# ── Panel with manage_focus ───────────────────────────────────────────────────

def test_panel_tab_moves_focus_forward() -> None:
    panel = Panel(RECT, manage_focus=True)
    w1 = make_focusable()
    w2 = make_focusable()
    panel.add(w1)
    panel.add(w2)
    panel.focus_first(panel._children)

    panel.handle_event(tab_event())
    assert w1.focused is False
    assert w2.focused is True


def test_panel_shift_tab_moves_focus_backward() -> None:
    panel = Panel(RECT, manage_focus=True)
    w1 = make_focusable()
    w2 = make_focusable()
    panel.add(w1)
    panel.add(w2)
    panel.focus_first(panel._children)

    panel.handle_event(tab_event(shift=True))
    assert w2.focused is True
    assert w1.focused is False


def test_panel_tab_wraps_around() -> None:
    panel = Panel(RECT, manage_focus=True)
    w1 = make_focusable()
    w2 = make_focusable()
    panel.add(w1)
    panel.add(w2)
    panel.focus_first(panel._children)

    panel.handle_event(tab_event())   # w1 → w2
    panel.handle_event(tab_event())   # w2 → w1 (wrap)
    assert w1.focused is True
    assert w2.focused is False


def test_panel_without_manage_focus_ignores_tab() -> None:
    panel = Panel(RECT, manage_focus=False)
    w1 = make_focusable()
    w2 = make_focusable()
    panel.add(w1)
    panel.add(w2)
    w1.focused = True

    consumed = panel.handle_event(tab_event())
    # Tab not consumed — panel not managing focus
    assert consumed is False


# ── Stack with manage_focus ───────────────────────────────────────────────────

def test_stack_tab_moves_focus_forward() -> None:
    stack = Stack(RECT, manage_focus=True)
    w1 = make_focusable()
    w2 = make_focusable()
    stack.add(w1)
    stack.add(w2)
    stack.focus_first(stack._children)

    stack.handle_event(tab_event())
    assert w2.focused is True


def test_stack_skips_non_focusable() -> None:
    stack = Stack(RECT, manage_focus=True)
    w1 = make_focusable()
    label = make_display()
    w2 = make_focusable()
    stack.add(w1)
    stack.add(label)
    stack.add(w2)
    stack.focus_first(stack._children)

    stack.handle_event(tab_event())
    assert label.focused is False
    assert w2.focused is True


# ── focus_first and focus_none ────────────────────────────────────────────────

def test_focus_first_sets_first_focusable() -> None:
    fm = FocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    fm.focus_first([w1, w2])
    assert w1.focused is True
    assert w2.focused is False


def test_focus_none_clears_all() -> None:
    fm = FocusManager()
    w1 = make_focusable()
    w2 = make_focusable()
    w1.focused = True
    fm._focus_index = 0
    fm.focus_none([w1, w2])
    assert w1.focused is False
    assert w2.focused is False
    assert fm._focus_index == -1


# ── No focusable children ─────────────────────────────────────────────────────

def test_tab_with_no_focusable_children_not_consumed() -> None:
    panel = Panel(RECT, manage_focus=True)
    panel.add(make_display())   # not focusable

    consumed = panel.handle_event(tab_event())
    assert consumed is False


def test_focus_first_with_no_focusable_does_nothing() -> None:
    fm = FocusManager()
    w = make_display()
    fm.focus_first([w])   # should not raise
    assert w.focused is False


# ── Widget.focusable default ──────────────────────────────────────────────────

def test_widget_focusable_defaults_false() -> None:
    w = Widget(RECT)
    assert w.focusable is False


def test_button_focusable_defaults_true() -> None:
    from pygame_engine.ui.controls.button import Button
    b = Button(pygame.Rect(0, 0, 100, 40), "Test")
    assert b.focusable is True


def test_input_field_focusable_defaults_true() -> None:
    from pygame_engine.ui.controls.input_field import InputField
    f = InputField(pygame.Rect(0, 0, 200, 40))
    assert f.focusable is True
