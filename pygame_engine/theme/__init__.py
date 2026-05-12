"""
pygame_engine.theme

Visual theme system: tokens, defaults, and runtime access.

Public API::

    from pygame_engine.theme import get_theme, set_theme, reset_theme
    from pygame_engine.theme import Theme
    from pygame_engine.theme import DEFAULT_THEME
"""

from pygame_engine.theme.defaults import DEFAULT_THEME, Theme
from pygame_engine.theme.runtime import get_theme, reset_theme, set_theme

__all__ = [
    "Theme",
    "DEFAULT_THEME",
    "get_theme",
    "set_theme",
    "reset_theme",
]
