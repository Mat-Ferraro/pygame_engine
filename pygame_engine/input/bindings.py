"""
Default mappings from physical pygame keys to engine action names.

A binding is a dict[int, str] where the key is a pygame key constant
and the value is an action string from actions.py.

Bindings are pure data — no logic lives here. Actions and bindings are
kept separate so bindings can be swapped or overridden per-project.

Runtime remapping
-----------------
Use ``InputManager.remap(action, key)`` to change a binding at runtime,
or replace ``InputManager.bindings`` wholesale.

Saving / loading
----------------
Use ``InputManager.bindings_to_dict()`` and
``InputManager.bindings_from_dict()`` to serialise bindings for persistence.

Controller bindings
-------------------
Controller button → action mappings live in a separate
``CONTROLLER_BINDINGS`` dict. Axes are configured via ``ControllerConfig``.
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

# Default controller button → action mapping (pygame joystick button indices)
DEFAULT_CONTROLLER_BINDINGS: dict[int, str] = {
    0:  actions.CONFIRM,    # A / Cross
    1:  actions.CANCEL,     # B / Circle
    7:  actions.PAUSE,      # Start / Options
    11: actions.NAV_UP,     # D-pad up
    12: actions.NAV_DOWN,   # D-pad down
    13: actions.NAV_LEFT,   # D-pad left
    14: actions.NAV_RIGHT,  # D-pad right
}

# Human-readable names for common pygame key constants (used in remapping UI)
KEY_NAMES: dict[int, str] = {
    pygame.K_RETURN:    "Enter",
    pygame.K_KP_ENTER:  "Numpad Enter",
    pygame.K_SPACE:     "Space",
    pygame.K_ESCAPE:    "Escape",
    pygame.K_UP:        "Up",
    pygame.K_DOWN:      "Down",
    pygame.K_LEFT:      "Left",
    pygame.K_RIGHT:     "Right",
    pygame.K_w:         "W",
    pygame.K_a:         "A",
    pygame.K_s:         "S",
    pygame.K_d:         "D",
    pygame.K_p:         "P",
    pygame.K_F1:        "F1",
    pygame.K_F2:        "F2",
    pygame.K_F3:        "F3",
}


def key_name(key: int) -> str:
    """Return a human-readable name for a pygame key constant."""
    return KEY_NAMES.get(key) or pygame.key.name(key).title()


# Controller button names for common indices
CONTROLLER_BUTTON_NAMES: dict[int, str] = {
    0:  "A / Cross",
    1:  "B / Circle",
    2:  "X / Square",
    3:  "Y / Triangle",
    4:  "LB / L1",
    5:  "RB / R1",
    6:  "Select / Share",
    7:  "Start / Options",
    8:  "L3",
    9:  "R3",
    10: "Guide",
    11: "D-pad Up",
    12: "D-pad Down",
    13: "D-pad Left",
    14: "D-pad Right",
}


def controller_button_name(button: int) -> str:
    """Return a human-readable name for a controller button index."""
    return CONTROLLER_BUTTON_NAMES.get(button, f"Button {button}")
