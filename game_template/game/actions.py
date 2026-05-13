"""
game/actions.py

Game-specific input action constants.

Re-exports engine actions for convenience, then defines game-specific
actions below. Import from here in all game scenes and systems so
you have one place to manage all action names.

Usage::

    from game.actions import CONFIRM, CANCEL, ATTACK, INTERACT
"""

# Re-export all engine actions so game code only needs one import
from pygame_engine.input.actions import (
    CANCEL,
    CONFIRM,
    CONSOLE_TOGGLE,
    DEBUG_TOGGLE,
    INSPECTOR_TOGGLE,
    NAV_DOWN,
    NAV_LEFT,
    NAV_RIGHT,
    NAV_UP,
    PAUSE,
)

# ── Game-specific actions ─────────────────────────────────────────────────────
# Define your game's custom actions here and add bindings in main.py

ATTACK    = "attack"
INTERACT  = "interact"
SPRINT    = "sprint"
INVENTORY = "inventory"
MAP       = "map"

__all__ = [
    # Engine actions
    "CONFIRM", "CANCEL", "PAUSE",
    "NAV_UP", "NAV_DOWN", "NAV_LEFT", "NAV_RIGHT",
    "DEBUG_TOGGLE", "INSPECTOR_TOGGLE", "CONSOLE_TOGGLE",
    # Game actions
    "ATTACK", "INTERACT", "SPRINT", "INVENTORY", "MAP",
]
