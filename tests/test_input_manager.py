"""
tests/test_input_manager.py

Tests for pygame_engine.input.InputManager.

Covers: keyboard press/release/held state, action queries, mouse button
state, wheel delta, binding replacement. Uses synthetic event lists to
drive update() without needing a display.
"""

import pygame

from pygame_engine.input import actions
from pygame_engine.input.bindings import DEFAULT_BINDINGS
from pygame_engine.input.input_manager import InputManager


def key_down(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN,
                              {"key": key, "mod": 0,
                               "unicode": "", "scancode": 0})

def key_up(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYUP,
                              {"key": key, "mod": 0,
                               "unicode": "", "scancode": 0})

def mouse_down(button: int = 1, pos=(0, 0)) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                              {"button": button, "pos": pos})

def mouse_up(button: int = 1, pos=(0, 0)) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONUP,
                              {"button": button, "pos": pos})

def mouse_move(pos=(10, 20)) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEMOTION,
                              {"pos": pos, "rel": (0, 0), "buttons": (0, 0, 0)})

def wheel(x=0, y=0) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEWHEEL,
                              {"x": x, "y": y, "flipped": False})


# ── Keyboard press state ──────────────────────────────────────────────────────

def test_key_not_pressed_initially() -> None:
    im = InputManager()
    assert im.was_key_pressed(pygame.K_SPACE) is False


def test_was_key_pressed_true_on_keydown_frame() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_SPACE)])
    assert im.was_key_pressed(pygame.K_SPACE) is True


def test_was_key_pressed_false_next_frame() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_SPACE)])
    im.update([])
    assert im.was_key_pressed(pygame.K_SPACE) is False


def test_is_key_down_true_while_held() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_LEFT)])
    im.update([])   # still held — no KEYUP
    assert im.is_key_down(pygame.K_LEFT) is True


def test_is_key_down_false_after_release() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_LEFT)])
    im.update([key_up(pygame.K_LEFT)])
    assert im.is_key_down(pygame.K_LEFT) is False


def test_was_key_released_true_on_keyup_frame() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_a)])
    im.update([key_up(pygame.K_a)])
    assert im.was_key_released(pygame.K_a) is True


def test_was_key_released_false_next_frame() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_a)])
    im.update([key_up(pygame.K_a)])
    im.update([])
    assert im.was_key_released(pygame.K_a) is False


def test_multiple_keys_tracked_independently() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_LEFT), key_down(pygame.K_UP)])
    assert im.is_key_down(pygame.K_LEFT) is True
    assert im.is_key_down(pygame.K_UP)   is True
    assert im.is_key_down(pygame.K_DOWN) is False


# ── Action queries ────────────────────────────────────────────────────────────

def test_was_action_pressed_confirm_on_return() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_RETURN)])
    assert im.was_action_pressed(actions.CONFIRM) is True


def test_was_action_pressed_false_when_not_pressed() -> None:
    im = InputManager()
    im.update([])
    assert im.was_action_pressed(actions.CONFIRM) is False


def test_is_action_down_true_while_held() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_w)])
    im.update([])
    assert im.is_action_down(actions.NAV_UP) is True


def test_is_action_down_false_after_release() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_w)])
    im.update([key_up(pygame.K_w)])
    assert im.is_action_down(actions.NAV_UP) is False


def test_was_action_released_on_keyup() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_ESCAPE)])
    im.update([key_up(pygame.K_ESCAPE)])
    assert im.was_action_released(actions.CANCEL) is True


def test_action_with_alternate_binding() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_KP_ENTER)])
    assert im.was_action_pressed(actions.CONFIRM) is True


# ── Mouse position ────────────────────────────────────────────────────────────

def test_mouse_position_updated_from_motion() -> None:
    im = InputManager()
    im.update([mouse_move((150, 200))])
    assert im.get_mouse_pos() == (150, 200)


def test_mouse_delta_calculated() -> None:
    im = InputManager()
    im.update([mouse_move((100, 100))])
    im.update([mouse_move((110, 115))])
    dx, dy = im.get_mouse_delta()
    assert dx == 10
    assert dy == 15


def test_mouse_delta_zero_when_no_movement() -> None:
    im = InputManager()
    im.update([mouse_move((50, 50))])
    im.update([])
    assert im.get_mouse_delta() == (0, 0)


# ── Mouse buttons ─────────────────────────────────────────────────────────────

def test_was_mouse_pressed_left_button() -> None:
    im = InputManager()
    im.update([mouse_down(1)])
    assert im.was_mouse_pressed(1) is True


def test_was_mouse_pressed_false_next_frame() -> None:
    im = InputManager()
    im.update([mouse_down(1)])
    im.update([])
    assert im.was_mouse_pressed(1) is False


def test_is_mouse_down_true_while_held() -> None:
    im = InputManager()
    im.update([mouse_down(1)])
    im.update([])
    assert im.is_mouse_down(1) is True


def test_is_mouse_down_false_after_release() -> None:
    im = InputManager()
    im.update([mouse_down(1)])
    im.update([mouse_up(1)])
    assert im.is_mouse_down(1) is False


def test_was_mouse_released_true_on_mouseup() -> None:
    im = InputManager()
    im.update([mouse_down(3)])
    im.update([mouse_up(3)])
    assert im.was_mouse_released(3) is True


def test_right_button_tracked_independently() -> None:
    im = InputManager()
    im.update([mouse_down(1)])
    assert im.was_mouse_pressed(1) is True
    assert im.was_mouse_pressed(3) is False


# ── Mouse wheel ───────────────────────────────────────────────────────────────

def test_wheel_delta_set_from_event() -> None:
    im = InputManager()
    im.update([wheel(x=0, y=2)])
    assert im.get_wheel_delta() == (0, 2)


def test_wheel_delta_cleared_next_frame() -> None:
    im = InputManager()
    im.update([wheel(x=0, y=3)])
    im.update([])
    assert im.get_wheel_delta() == (0, 0)


def test_wheel_horizontal() -> None:
    im = InputManager()
    im.update([wheel(x=-1, y=0)])
    assert im.get_wheel_delta() == (-1, 0)


# ── Bindings ──────────────────────────────────────────────────────────────────

def test_custom_bindings_replace_defaults() -> None:
    custom = {pygame.K_z: actions.CONFIRM}
    im = InputManager(bindings=custom)
    im.update([key_down(pygame.K_z)])
    assert im.was_action_pressed(actions.CONFIRM) is True


def test_bindings_setter_takes_effect_next_frame() -> None:
    im = InputManager()
    im.bindings = {pygame.K_q: actions.CANCEL}
    im.update([key_down(pygame.K_q)])
    assert im.was_action_pressed(actions.CANCEL) is True


def test_transient_state_cleared_each_frame() -> None:
    im = InputManager()
    im.update([key_down(pygame.K_SPACE)])
    assert im.was_key_pressed(pygame.K_SPACE) is True
    im.update([])
    assert im.was_key_pressed(pygame.K_SPACE) is False
    assert im.was_key_released(pygame.K_SPACE) is False
