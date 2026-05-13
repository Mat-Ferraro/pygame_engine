"""
tests/test_input_manager.py

Tests for pygame_engine.input.InputManager.
Covers keyboard, mouse, remapping, serialisation, and controller queries
(headless — no real joystick needed).
"""

import pygame
import pytest

from pygame_engine.input import actions
from pygame_engine.input.bindings import DEFAULT_BINDINGS
from pygame_engine.input.input_manager import ControllerConfig, InputManager


# ── Event helpers ─────────────────────────────────────────────────────────────

def key_down(key):
    return pygame.event.Event(pygame.KEYDOWN,
                              {"key": key, "mod": 0, "unicode": "", "scancode": 0})

def key_up(key):
    return pygame.event.Event(pygame.KEYUP,
                              {"key": key, "mod": 0, "unicode": "", "scancode": 0})

def mouse_down(button=1, pos=(0, 0)):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": button, "pos": pos})

def mouse_up(button=1, pos=(0, 0)):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": button, "pos": pos})

def mouse_move(pos=(10, 20)):
    return pygame.event.Event(pygame.MOUSEMOTION,
                              {"pos": pos, "rel": (0, 0), "buttons": (0, 0, 0)})

def wheel(x=0, y=0):
    return pygame.event.Event(pygame.MOUSEWHEEL, {"x": x, "y": y, "flipped": False})

def joy_button_down(instance_id, button):
    return pygame.event.Event(pygame.JOYBUTTONDOWN,
                              {"instance_id": instance_id, "button": button})

def joy_button_up(instance_id, button):
    return pygame.event.Event(pygame.JOYBUTTONUP,
                              {"instance_id": instance_id, "button": button})

def joy_axis(instance_id, axis, value):
    return pygame.event.Event(pygame.JOYAXISMOTION,
                              {"instance_id": instance_id,
                               "axis": axis, "value": value})


# ══════════════════════════════════════════════════════════════════════════════
# Keyboard
# ══════════════════════════════════════════════════════════════════════════════

def test_key_not_pressed_initially():
    assert InputManager().was_key_pressed(pygame.K_SPACE) is False

def test_was_key_pressed_true_on_keydown_frame():
    im = InputManager()
    im.update([key_down(pygame.K_SPACE)])
    assert im.was_key_pressed(pygame.K_SPACE) is True

def test_was_key_pressed_false_next_frame():
    im = InputManager()
    im.update([key_down(pygame.K_SPACE)])
    im.update([])
    assert im.was_key_pressed(pygame.K_SPACE) is False

def test_is_key_down_true_while_held():
    im = InputManager()
    im.update([key_down(pygame.K_LEFT)])
    im.update([])
    assert im.is_key_down(pygame.K_LEFT) is True

def test_is_key_down_false_after_release():
    im = InputManager()
    im.update([key_down(pygame.K_LEFT)])
    im.update([key_up(pygame.K_LEFT)])
    assert im.is_key_down(pygame.K_LEFT) is False

def test_was_key_released_true_on_keyup_frame():
    im = InputManager()
    im.update([key_down(pygame.K_a)])
    im.update([key_up(pygame.K_a)])
    assert im.was_key_released(pygame.K_a) is True

def test_was_key_released_false_next_frame():
    im = InputManager()
    im.update([key_down(pygame.K_a)])
    im.update([key_up(pygame.K_a)])
    im.update([])
    assert im.was_key_released(pygame.K_a) is False

def test_multiple_keys_tracked_independently():
    im = InputManager()
    im.update([key_down(pygame.K_LEFT), key_down(pygame.K_UP)])
    assert im.is_key_down(pygame.K_LEFT) is True
    assert im.is_key_down(pygame.K_UP)   is True
    assert im.is_key_down(pygame.K_DOWN) is False


# ══════════════════════════════════════════════════════════════════════════════
# Action queries (keyboard)
# ══════════════════════════════════════════════════════════════════════════════

def test_was_action_pressed_confirm_on_return():
    im = InputManager()
    im.update([key_down(pygame.K_RETURN)])
    assert im.was_action_pressed(actions.CONFIRM) is True

def test_was_action_pressed_false_when_not_pressed():
    im = InputManager()
    im.update([])
    assert im.was_action_pressed(actions.CONFIRM) is False

def test_is_action_down_true_while_held():
    im = InputManager()
    im.update([key_down(pygame.K_w)])
    im.update([])
    assert im.is_action_down(actions.NAV_UP) is True

def test_is_action_down_false_after_release():
    im = InputManager()
    im.update([key_down(pygame.K_w)])
    im.update([key_up(pygame.K_w)])
    assert im.is_action_down(actions.NAV_UP) is False

def test_was_action_released_on_keyup():
    im = InputManager()
    im.update([key_down(pygame.K_ESCAPE)])
    im.update([key_up(pygame.K_ESCAPE)])
    assert im.was_action_released(actions.CANCEL) is True

def test_action_with_alternate_binding():
    im = InputManager()
    im.update([key_down(pygame.K_KP_ENTER)])
    assert im.was_action_pressed(actions.CONFIRM) is True


# ══════════════════════════════════════════════════════════════════════════════
# Mouse
# ══════════════════════════════════════════════════════════════════════════════

def test_mouse_position_updated_from_motion():
    im = InputManager()
    im.update([mouse_move((150, 200))])
    assert im.get_mouse_pos() == (150, 200)

def test_mouse_delta_calculated():
    im = InputManager()
    im.update([mouse_move((100, 100))])
    im.update([mouse_move((110, 115))])
    assert im.get_mouse_delta() == (10, 15)

def test_mouse_delta_zero_when_no_movement():
    im = InputManager()
    im.update([mouse_move((50, 50))])
    im.update([])
    assert im.get_mouse_delta() == (0, 0)

def test_was_mouse_pressed_left_button():
    im = InputManager()
    im.update([mouse_down(1)])
    assert im.was_mouse_pressed(1) is True

def test_was_mouse_pressed_false_next_frame():
    im = InputManager()
    im.update([mouse_down(1)])
    im.update([])
    assert im.was_mouse_pressed(1) is False

def test_is_mouse_down_true_while_held():
    im = InputManager()
    im.update([mouse_down(1)])
    im.update([])
    assert im.is_mouse_down(1) is True

def test_is_mouse_down_false_after_release():
    im = InputManager()
    im.update([mouse_down(1)])
    im.update([mouse_up(1)])
    assert im.is_mouse_down(1) is False

def test_was_mouse_released_true_on_mouseup():
    im = InputManager()
    im.update([mouse_down(3)])
    im.update([mouse_up(3)])
    assert im.was_mouse_released(3) is True

def test_right_button_tracked_independently():
    im = InputManager()
    im.update([mouse_down(1)])
    assert im.was_mouse_pressed(1) is True
    assert im.was_mouse_pressed(3) is False

def test_wheel_delta_set_from_event():
    im = InputManager()
    im.update([wheel(x=0, y=2)])
    assert im.get_wheel_delta() == (0, 2)

def test_wheel_delta_cleared_next_frame():
    im = InputManager()
    im.update([wheel(x=0, y=3)])
    im.update([])
    assert im.get_wheel_delta() == (0, 0)

def test_wheel_horizontal():
    im = InputManager()
    im.update([wheel(x=-1, y=0)])
    assert im.get_wheel_delta() == (-1, 0)


# ══════════════════════════════════════════════════════════════════════════════
# Key remapping
# ══════════════════════════════════════════════════════════════════════════════

def test_custom_bindings_replace_defaults():
    im = InputManager(bindings={pygame.K_z: actions.CONFIRM})
    im.update([key_down(pygame.K_z)])
    assert im.was_action_pressed(actions.CONFIRM) is True

def test_bindings_setter_takes_effect_next_frame():
    im = InputManager()
    im.bindings = {pygame.K_q: actions.CANCEL}
    im.update([key_down(pygame.K_q)])
    assert im.was_action_pressed(actions.CANCEL) is True

def test_transient_state_cleared_each_frame():
    im = InputManager()
    im.update([key_down(pygame.K_SPACE)])
    assert im.was_key_pressed(pygame.K_SPACE) is True
    im.update([])
    assert im.was_key_pressed(pygame.K_SPACE)   is False
    assert im.was_key_released(pygame.K_SPACE)  is False

def test_remap_changes_binding():
    im = InputManager()
    im.remap(actions.CONFIRM, pygame.K_z)
    im.update([key_down(pygame.K_z)])
    assert im.was_action_pressed(actions.CONFIRM) is True

def test_remap_removes_old_binding():
    im = InputManager()
    im.remap(actions.CONFIRM, pygame.K_z)
    # Old keys (RETURN, SPACE, etc.) should no longer trigger CONFIRM
    im.update([key_down(pygame.K_RETURN)])
    assert im.was_action_pressed(actions.CONFIRM) is False

def test_get_key_for_action_returns_bound_key():
    im = InputManager()
    im.remap(actions.CONFIRM, pygame.K_z)
    assert im.get_key_for_action(actions.CONFIRM) == pygame.K_z

def test_get_key_for_action_none_when_unbound():
    im = InputManager(bindings={})
    assert im.get_key_for_action(actions.CONFIRM) is None

def test_reset_to_defaults_restores_bindings():
    im = InputManager()
    im.remap(actions.CONFIRM, pygame.K_z)
    im.reset_to_defaults()
    # RETURN should work again
    im.update([key_down(pygame.K_RETURN)])
    assert im.was_action_pressed(actions.CONFIRM) is True


# ══════════════════════════════════════════════════════════════════════════════
# Serialisation
# ══════════════════════════════════════════════════════════════════════════════

def test_bindings_to_dict_produces_serialisable_dict():
    im = InputManager()
    d  = im.bindings_to_dict()
    assert "keyboard"   in d
    assert "controller" in d
    # All keys must be string-serialisable ints
    for k in d["keyboard"]:
        int(k)   # should not raise

def test_bindings_from_dict_restores_bindings():
    im1 = InputManager()
    im1.remap(actions.CONFIRM, pygame.K_z)
    saved = im1.bindings_to_dict()

    im2 = InputManager()
    im2.bindings_from_dict(saved)
    im2.update([key_down(pygame.K_z)])
    assert im2.was_action_pressed(actions.CONFIRM) is True

def test_bindings_roundtrip_preserves_controller_bindings():
    im1 = InputManager()
    im1.remap_controller(actions.CONFIRM, 2)
    saved = im1.bindings_to_dict()

    im2 = InputManager()
    im2.bindings_from_dict(saved)
    assert im2.get_button_for_action(actions.CONFIRM) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Controller (synthetic events — no real hardware needed)
# ══════════════════════════════════════════════════════════════════════════════

def test_controller_count_zero_initially():
    im = InputManager()
    # We can't guarantee no real controllers in CI, just check type
    assert isinstance(im.controller_count, int)

def test_controller_button_pressed_via_event():
    im = InputManager()
    im.update([joy_button_down(instance_id=0, button=0)])
    assert im.was_controller_button_pressed(0) is True

def test_controller_button_pressed_false_next_frame():
    im = InputManager()
    im.update([joy_button_down(instance_id=0, button=0)])
    im.update([])
    assert im.was_controller_button_pressed(0) is False

def test_controller_button_down_while_held():
    im = InputManager()
    im.update([joy_button_down(instance_id=0, button=0)])
    im.update([])
    assert im.is_controller_button_down(0) is True

def test_controller_button_released():
    im = InputManager()
    im.update([joy_button_down(instance_id=0, button=0)])
    im.update([joy_button_up(instance_id=0, button=0)])
    assert im.is_controller_button_down(0) is False

def test_controller_action_from_button():
    im = InputManager()
    im.update([joy_button_down(instance_id=0, button=0)])  # 0 = CONFIRM
    assert im.was_action_pressed(actions.CONFIRM) is True

def test_controller_axis_action_nav_right():
    im = InputManager()
    im.update([joy_axis(instance_id=0, axis=0, value=0.8)])
    assert im.is_action_down(actions.NAV_RIGHT) is True

def test_controller_axis_action_nav_left():
    im = InputManager()
    im.update([joy_axis(instance_id=0, axis=0, value=-0.8)])
    assert im.is_action_down(actions.NAV_LEFT) is True

def test_controller_axis_dead_zone_no_action():
    im = InputManager(controller_config=ControllerConfig(dead_zone=0.15))
    im.update([joy_axis(instance_id=0, axis=0, value=0.1)])
    assert im.is_action_down(actions.NAV_RIGHT) is False

def test_controller_axis_pressed_fires_once():
    im = InputManager()
    im.update([joy_axis(instance_id=0, axis=0, value=0.8)])
    assert im.was_action_pressed(actions.NAV_RIGHT) is True
    im.update([joy_axis(instance_id=0, axis=0, value=0.8)])
    assert im.was_action_pressed(actions.NAV_RIGHT) is False  # still held, not new

def test_get_axis_returns_dead_zone_filtered_value():
    im = InputManager(controller_config=ControllerConfig(dead_zone=0.15))
    im.update([joy_axis(instance_id=0, axis=0, value=0.05)])
    assert im.get_axis(0, 0) == 0.0   # below dead zone

def test_controller_remap_button():
    im = InputManager()
    im.remap_controller(actions.CANCEL, 1)
    im.update([joy_button_down(instance_id=0, button=1)])
    assert im.was_action_pressed(actions.CANCEL) is True

def test_get_button_for_action():
    im = InputManager()
    assert im.get_button_for_action(actions.CONFIRM) == 0  # default A button


# ══════════════════════════════════════════════════════════════════════════════
# Haptic feedback (rumble)
# ══════════════════════════════════════════════════════════════════════════════

class _MockJoystick:
    """Minimal joystick stub for rumble testing."""
    def __init__(self, instance_id=0):
        self._id        = instance_id
        self.rumble_calls:      list = []
        self.stop_rumble_calls: int  = 0

    def get_instance_id(self): return self._id
    def get_name(self):        return "Mock Controller"

    def rumble(self, low, high, duration_ms):
        self.rumble_calls.append((low, high, duration_ms))

    def stop_rumble(self):
        self.stop_rumble_calls += 1


def _im_with_mock_joy(instance_id=0):
    im  = InputManager()
    joy = _MockJoystick(instance_id)
    im._joysticks[instance_id] = joy
    return im, joy


def test_rumble_calls_joystick_rumble():
    im, joy = _im_with_mock_joy()
    im.rumble(low=0.3, high=0.8, duration_ms=200)
    assert len(joy.rumble_calls) == 1
    assert joy.rumble_calls[0] == (0.3, 0.8, 200)


def test_rumble_default_values():
    im, joy = _im_with_mock_joy()
    im.rumble()
    assert joy.rumble_calls[0] == (0.5, 0.5, 200)


def test_rumble_targets_specific_joystick():
    im = InputManager()
    joy0 = _MockJoystick(0); im._joysticks[0] = joy0
    joy1 = _MockJoystick(1); im._joysticks[1] = joy1
    im.rumble(low=1.0, high=0.0, duration_ms=100, joystick_id=0)
    assert len(joy0.rumble_calls) == 1
    assert len(joy1.rumble_calls) == 0


def test_rumble_all_joysticks_when_no_id():
    im = InputManager()
    joy0 = _MockJoystick(0); im._joysticks[0] = joy0
    joy1 = _MockJoystick(1); im._joysticks[1] = joy1
    im.rumble(0.5, 0.5, 150)
    assert len(joy0.rumble_calls) == 1
    assert len(joy1.rumble_calls) == 1


def test_rumble_no_controllers_does_not_raise():
    im = InputManager()   # no joysticks
    im.rumble(0.5, 0.5, 200)   # should not raise


def test_rumble_unknown_joystick_id_does_not_raise():
    im, _ = _im_with_mock_joy(0)
    im.rumble(joystick_id=99)   # id 99 not present — silent


def test_stop_rumble_calls_joystick_stop():
    im, joy = _im_with_mock_joy()
    im.stop_rumble()
    assert joy.stop_rumble_calls == 1


def test_stop_rumble_targets_specific_joystick():
    im = InputManager()
    joy0 = _MockJoystick(0); im._joysticks[0] = joy0
    joy1 = _MockJoystick(1); im._joysticks[1] = joy1
    im.stop_rumble(joystick_id=1)
    assert joy0.stop_rumble_calls == 0
    assert joy1.stop_rumble_calls == 1


def test_stop_rumble_all_joysticks():
    im = InputManager()
    joy0 = _MockJoystick(0); im._joysticks[0] = joy0
    joy1 = _MockJoystick(1); im._joysticks[1] = joy1
    im.stop_rumble()
    assert joy0.stop_rumble_calls == 1
    assert joy1.stop_rumble_calls == 1


def test_stop_rumble_no_controllers_does_not_raise():
    InputManager().stop_rumble()


def test_rumble_graceful_on_unsupported_controller():
    """Controllers that don't support rumble raise — must be swallowed."""
    class _NoRumbleJoy(_MockJoystick):
        def rumble(self, *a): raise pygame.error("not supported")
        def stop_rumble(self):  raise pygame.error("not supported")

    im  = InputManager()
    joy = _NoRumbleJoy(0)
    im._joysticks[0] = joy
    im.rumble(0.5, 0.5, 100)    # must not raise
    im.stop_rumble()             # must not raise
