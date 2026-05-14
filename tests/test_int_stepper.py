"""Tests for IntStepper widget."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

pygame.init()
pygame.display.set_mode((800, 600))

from pygame_engine.ui.controls.int_stepper import IntStepper


def make_stepper(**kwargs):
    defaults = dict(rect=pygame.Rect(0, 0, 240, 60), value=5,
                    min_value=1, max_value=10)
    defaults.update(kwargs)
    return IntStepper(**defaults)


def ev(type_, **kwargs):
    return pygame.event.Event(type_, **kwargs)


# ── Construction ──────────────────────────────────────────────────────────────

def test_initial_value():
    s = make_stepper(value=3)
    assert s.value == 3


def test_value_clamped_to_min_on_construction():
    s = make_stepper(value=0, min_value=1)
    assert s.value == 1


def test_value_clamped_to_max_on_construction():
    s = make_stepper(value=99, max_value=10)
    assert s.value == 10


def test_label_attribute():
    s = make_stepper(label="Campaigns")
    assert s.label == "Campaigns"


def test_fmt_attribute():
    s = make_stepper(fmt="{v}g")
    assert s.fmt == "{v}g"


# ── Increment / decrement ─────────────────────────────────────────────────────

def test_increment_increases_value():
    s = make_stepper(value=5)
    s.increment()
    assert s.value == 6


def test_decrement_decreases_value():
    s = make_stepper(value=5)
    s.decrement()
    assert s.value == 4


def test_increment_does_not_exceed_max():
    s = make_stepper(value=10, max_value=10)
    s.increment()
    assert s.value == 10


def test_decrement_does_not_go_below_min():
    s = make_stepper(value=1, min_value=1)
    s.decrement()
    assert s.value == 1


def test_step_applied_correctly():
    s = make_stepper(value=4, step=2, min_value=0, max_value=20)
    s.increment()
    assert s.value == 6


def test_set_value_directly():
    s = make_stepper(value=5)
    s.value = 8
    assert s.value == 8


def test_set_value_clamps():
    s = make_stepper(min_value=1, max_value=10)
    s.value = 99
    assert s.value == 10
    s.value = -5
    assert s.value == 1


# ── on_change callback ────────────────────────────────────────────────────────

def test_on_change_fires_on_increment():
    log = []
    s = make_stepper(value=3, on_change=lambda v: log.append(v))
    s.increment()
    assert log == [4]


def test_on_change_fires_on_decrement():
    log = []
    s = make_stepper(value=5, on_change=lambda v: log.append(v))
    s.decrement()
    assert log == [4]


def test_on_change_not_fired_when_at_boundary():
    log = []
    s = make_stepper(value=1, min_value=1, on_change=lambda v: log.append(v))
    s.decrement()
    assert log == []


def test_on_change_not_fired_when_value_unchanged():
    log = []
    s = make_stepper(value=5, on_change=lambda v: log.append(v))
    s.value = 5
    assert log == []


# ── Keyboard ──────────────────────────────────────────────────────────────────

def test_right_key_increments():
    s = make_stepper(value=4)
    s.focused = True
    s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode=""))
    assert s.value == 5


def test_left_key_decrements():
    s = make_stepper(value=4)
    s.focused = True
    s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_LEFT, mod=0, unicode=""))
    assert s.value == 3


def test_up_key_increments():
    s = make_stepper(value=4)
    s.focused = True
    s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_UP, mod=0, unicode=""))
    assert s.value == 5


def test_down_key_decrements():
    s = make_stepper(value=4)
    s.focused = True
    s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode=""))
    assert s.value == 3


def test_keyboard_ignored_when_not_focused():
    s = make_stepper(value=5)
    s.focused = False
    s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode=""))
    assert s.value == 5


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_does_not_raise():
    surf = pygame.Surface((400, 200))
    s = make_stepper(label="Test Label", fmt="{v}c")
    s.render(surf)


def test_render_invisible_skips():
    surf = pygame.Surface((400, 200))
    surf.fill((5, 5, 5))
    s = make_stepper()
    s.visible = False
    s.render(surf)
    assert surf.get_at((0, 0)) == (5, 5, 5, 255)


def test_render_no_label_does_not_raise():
    surf = pygame.Surface((400, 200))
    s = make_stepper(label="")
    s.render(surf)


def test_btn_rects_are_inside_widget():
    s = make_stepper(rect=pygame.Rect(50, 50, 240, 60))
    dec_r, inc_r = s._btn_rects()
    assert s.rect.contains(dec_r)
    assert s.rect.contains(inc_r)


def test_value_rect_between_buttons():
    s = make_stepper(rect=pygame.Rect(0, 0, 240, 60))
    dec_r, inc_r = s._btn_rects()
    val_r = s._value_rect()
    assert val_r.left >= dec_r.right
    assert val_r.right <= inc_r.left
