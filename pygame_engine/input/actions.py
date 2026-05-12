"""
input/actions.py

Canonical action identifiers for pygame_engine.

Actions represent intent, not physical input. Scenes and widgets query
actions; bindings.py maps physical keys to these names.

Rules:
- Action names are plain strings (no enum overhead, easy to extend).
- Names describe what the player/user intends, not which key they pressed.
- Physical device details belong in bindings.py, not here.

Adding project-specific actions:
    In your game project, define extra action constants alongside these
    rather than modifying the engine directly::

        from pygame_engine.input.actions import CONFIRM, CANCEL
        ATTACK  = "attack"
        INTERACT = "interact"
"""

# ── Navigation ────────────────────────────────────────────────────────────────

NAV_UP    = "nav_up"
NAV_DOWN  = "nav_down"
NAV_LEFT  = "nav_left"
NAV_RIGHT = "nav_right"

# ── Confirmation ──────────────────────────────────────────────────────────────

CONFIRM = "confirm"
CANCEL  = "cancel"

# ── Application ───────────────────────────────────────────────────────────────

PAUSE = "pause"

# ── Debug (engine-reserved) ───────────────────────────────────────────────────

DEBUG_TOGGLE     = "debug_toggle"
INSPECTOR_TOGGLE = "inspector_toggle"
CONSOLE_TOGGLE   = "console_toggle"

# ── Convenience set ───────────────────────────────────────────────────────────

ALL_ACTIONS: frozenset[str] = frozenset({
    NAV_UP, NAV_DOWN, NAV_LEFT, NAV_RIGHT,
    CONFIRM, CANCEL,
    PAUSE,
    DEBUG_TOGGLE, INSPECTOR_TOGGLE, CONSOLE_TOGGLE,
})
