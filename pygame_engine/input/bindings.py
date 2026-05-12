"""
input/bindings.py

Default mappings from physical pygame keys to engine action names.

A binding is a dict[int, str] where the key is a pygame key constant
(e.g. pygame.K_RETURN) and the value is an action string from actions.py.

Design rules:
- Bindings are pure data — no logic lives here.
- Actions and bindings are kept separate so bindings can be swapped or
  overridden per-project without touching action definitions.
- Mouse buttons are NOT mapped to actions here. Widgets handle mouse
  interaction directly via hit-testing; actions are for intent-based
  keyboard/gamepad input.

Overriding bindings:
    Pass a custom binding dict to InputManager at construction, or replace
    InputManager.bindings at runtime before the first frame::

        from pygame_engine.input.bindings import DEFAULT_BINDINGS
        from pygame_engine.input import actions

        my_bindings = {**DEFAULT_BINDINGS, pygame.K_z: actions.CONFIRM}
        input_manager = InputManager(bindings=my_bindings)
"""

import pygame

from pygame_engine.input import actions


DEFAULT_BINDINGS: dict[int, str] = {

    # ── Confirm / cancel ──────────────────────────────────────────────────────
    pygame.K_RETURN:    actions.CONFIRM,
    pygame.K_KP_ENTER:  actions.CONFIRM,
    pygame.K_SPACE:     actions.CONFIRM,
    pygame.K_ESCAPE:    actions.CANCEL,

    # ── Navigation ────────────────────────────────────────────────────────────
    pygame.K_UP:        actions.NAV_UP,
    pygame.K_w:         actions.NAV_UP,
    pygame.K_DOWN:      actions.NAV_DOWN,
    pygame.K_s:         actions.NAV_DOWN,
    pygame.K_LEFT:      actions.NAV_LEFT,
    pygame.K_a:         actions.NAV_LEFT,
    pygame.K_RIGHT:     actions.NAV_RIGHT,
    pygame.K_d:         actions.NAV_RIGHT,

    # ── Application ───────────────────────────────────────────────────────────
    pygame.K_p:         actions.PAUSE,

    # ── Debug (engine-reserved) ───────────────────────────────────────────────
    pygame.K_F1:        actions.DEBUG_TOGGLE,
    pygame.K_F2:        actions.INSPECTOR_TOGGLE,
    pygame.K_F3:        actions.CONSOLE_TOGGLE,
}
