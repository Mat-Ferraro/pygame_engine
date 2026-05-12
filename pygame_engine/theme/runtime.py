"""
theme/runtime.py

Active theme access for pygame_engine.

This module is the single stable access point for the current theme.
Widgets, scenes, and any other engine code that needs style values
should import and call ``get_theme()`` here — never import
``DEFAULT_THEME`` from defaults.py directly.

Why a module-level accessor rather than injection
-------------------------------------------------
Widgets are created in many places (scene.on_enter, container children,
factory functions). Passing a theme object into every constructor adds
friction and verbosity with no real benefit in a personal framework
where all call sites are controlled.

``get_theme()`` always returns the current active theme. If a project
calls ``set_theme(my_theme)`` at startup, all subsequent ``get_theme()``
calls return the new theme automatically — no widgets need updating.

Usage::

    # Reading the theme (in a widget, scene, or helper):
    from pygame_engine.theme.runtime import get_theme

    theme = get_theme()
    colour = theme.button.normal.bg
    font_size = theme.typography.md

    # Setting a custom theme (once, at app startup):
    from pygame_engine.theme.runtime import set_theme
    from pygame_engine.theme.defaults import Theme

    set_theme(Theme(...))   # or a subclass / dataclass-replace

    # Resetting to the engine default:
    from pygame_engine.theme.runtime import reset_theme

    reset_theme()
"""

from __future__ import annotations

from pygame_engine.theme.defaults import DEFAULT_THEME, Theme

# Module-level state — the single active theme instance.
_active_theme: Theme = DEFAULT_THEME


def get_theme() -> Theme:
    """
    Return the currently active theme.

    Called each frame by widgets that need style values. Lightweight —
    just returns a module-level reference; no computation performed.
    """
    return _active_theme


def set_theme(theme: Theme) -> None:
    """
    Replace the active theme.

    Takes effect immediately. All subsequent calls to ``get_theme()``
    return the new theme. Safe to call before or after ``Application.run()``.

    Args:
        theme: The new theme to activate. Must be a ``Theme`` instance
               (or a subclass / dataclass-replaced variant).
    """
    global _active_theme
    _active_theme = theme


def reset_theme() -> None:
    """
    Restore the engine's built-in default theme.

    Equivalent to ``set_theme(DEFAULT_THEME)``.
    """
    global _active_theme
    _active_theme = DEFAULT_THEME
