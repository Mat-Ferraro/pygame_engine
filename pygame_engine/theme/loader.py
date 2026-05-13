"""
File-driven theme loading for pygame_engine.

Loads a JSON theme file and merges it over the default theme, allowing
designers to iterate on visual style without touching Python code.

JSON format
-----------
The JSON file is a partial theme — only the keys you want to override.
Unspecified keys retain their default values::

    {
        "colours": {
            "bg_base":   [18, 18, 26],
            "bg_raised": [28, 28, 40],
            "text":      [230, 230, 235]
        },
        "typography": {
            "family": "consolas,courier new,monospace",
            "md": 16
        },
        "button": {
            "normal":  {"bg": [60, 100, 180], "radius": 4},
            "hovered": {"bg": [80, 130, 220]},
            "padding": 10
        },
        "panel": {
            "surface": {"bg": [32, 36, 52], "border": [55, 60, 80]},
            "padding": 16
        },
        "spacing": {
            "xl": 28
        }
    }

Usage::

    from pygame_engine.theme.loader import theme_from_file
    from pygame_engine.theme.runtime import set_theme

    theme = theme_from_file(Path("assets/theme.json"))
    set_theme(theme)

    # Hot-reload during development (call each frame or on file change):
    from pygame_engine.theme.loader import reload_theme_file
    reload_theme_file(Path("assets/theme.json"))
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import fields
from pathlib import Path
from typing import Any

from pygame_engine.theme.defaults import (
    DEFAULT_THEME,
    ButtonTheme,
    ColoursTheme,
    LabelTheme,
    PanelTheme,
    SpacingTheme,
    SurfaceStyle,
    TextStyle,
    Theme,
    TypographyTheme,
)
from pygame_engine.theme.runtime import set_theme


def theme_from_file(path: Path) -> Theme:
    """
    Load a JSON theme file and return a Theme with overrides applied.

    The JSON file is merged over the default theme — only keys present
    in the file are overridden; everything else keeps its default value.

    Args:
        path: Path to the ``.json`` theme file.

    Returns:
        A new ``Theme`` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"Theme file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in theme file {path}: {e}") from e

    return _apply_overrides(deepcopy(DEFAULT_THEME), data)


def reload_theme_file(path: Path) -> Theme:
    """
    Load a JSON theme file and immediately activate it.

    Convenience wrapper that calls ``theme_from_file()`` then
    ``set_theme()``. Safe to call every frame during development —
    the file is re-read each call, so keep it in a dev-only path.

    Args:
        path: Path to the ``.json`` theme file.

    Returns:
        The newly activated ``Theme``.
    """
    theme = theme_from_file(path)
    set_theme(theme)
    return theme


def theme_to_dict(theme: Theme) -> dict:
    """
    Serialise a Theme to a JSON-compatible dict.

    Useful for inspecting the active theme or generating a starter file:

        import json
        print(json.dumps(theme_to_dict(get_theme()), indent=2))

    Args:
        theme: The Theme to serialise.

    Returns:
        A plain dict suitable for ``json.dumps()``.
    """
    return _theme_to_dict(theme)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _apply_overrides(theme: Theme, data: dict) -> Theme:
    """Recursively apply a dict of overrides onto a Theme dataclass tree."""

    if "colours" in data:
        theme.colours    = _apply_colours(theme.colours, data["colours"])
    if "typography" in data:
        theme.typography = _apply_typography(theme.typography, data["typography"])
    if "spacing" in data:
        theme.spacing    = _apply_spacing(theme.spacing, data["spacing"])
    if "button" in data:
        theme.button     = _apply_button(theme.button, data["button"])
    if "label" in data:
        theme.label      = _apply_label(theme.label, data["label"])
    if "panel" in data:
        theme.panel      = _apply_panel(theme.panel, data["panel"])

    return theme


def _rgb(value: Any) -> tuple[int, int, int]:
    """Accept [r, g, b] list or (r, g, b) tuple, return tuple."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    raise ValueError(f"Expected [r, g, b] list, got: {value!r}")


def _apply_colours(c: ColoursTheme, d: dict) -> ColoursTheme:
    colour_fields = {f.name for f in fields(c)}
    for key, val in d.items():
        if key in colour_fields:
            setattr(c, key, _rgb(val))
    return c


def _apply_typography(t: TypographyTheme, d: dict) -> TypographyTheme:
    if "family" in d: t.family = str(d["family"])
    for size in ("xs", "sm", "md", "lg", "xl", "xxl"):
        if size in d: setattr(t, size, int(d[size]))
    return t


def _apply_spacing(s: SpacingTheme, d: dict) -> SpacingTheme:
    for key in ("xs", "sm", "md", "lg", "xl", "xxl"):
        if key in d: setattr(s, key, int(d[key]))
    return s


def _apply_surface(surf: SurfaceStyle, d: dict) -> SurfaceStyle:
    if "bg"           in d: surf.bg           = _rgb(d["bg"])
    if "border"       in d: surf.border       = _rgb(d["border"])
    if "border_width" in d: surf.border_width = int(d["border_width"])
    if "radius"       in d: surf.radius       = int(d["radius"])
    return surf


def _apply_text_style(ts: TextStyle, d: dict) -> TextStyle:
    if "colour"      in d: ts.colour      = _rgb(d["colour"])
    if "font_size"   in d: ts.font_size   = int(d["font_size"])
    if "font_family" in d: ts.font_family = str(d["font_family"])
    if "bold"        in d: ts.bold        = bool(d["bold"])
    return ts


def _apply_button(b: ButtonTheme, d: dict) -> ButtonTheme:
    for state in ("normal", "hovered", "pressed", "disabled"):
        if state in d: _apply_surface(getattr(b, state), d[state])
    if "text"          in d: _apply_text_style(b.text,          d["text"])
    if "text_disabled" in d: _apply_text_style(b.text_disabled, d["text_disabled"])
    if "padding"       in d: b.padding = int(d["padding"])
    return b


def _apply_label(la: LabelTheme, d: dict) -> LabelTheme:
    if "text"           in d: _apply_text_style(la.text,           d["text"])
    if "secondary_text" in d: _apply_text_style(la.secondary_text, d["secondary_text"])
    return la


def _apply_panel(p: PanelTheme, d: dict) -> PanelTheme:
    if "surface" in d: _apply_surface(p.surface, d["surface"])
    if "padding" in d: p.padding = int(d["padding"])
    return p


def _theme_to_dict(theme: Theme) -> dict:
    """Recursively convert a Theme dataclass tree to a plain dict."""
    def _surf(s: SurfaceStyle) -> dict:
        return {"bg": list(s.bg), "border": list(s.border),
                "border_width": s.border_width, "radius": s.radius}

    def _text(t: TextStyle) -> dict:
        return {"colour": list(t.colour), "font_size": t.font_size,
                "font_family": t.font_family, "bold": t.bold}

    return {
        "colours": {f.name: list(getattr(theme.colours, f.name))
                    for f in fields(theme.colours)},
        "typography": {
            "family": theme.typography.family,
            **{s: getattr(theme.typography, s)
               for s in ("xs","sm","md","lg","xl","xxl")},
        },
        "spacing": {s: getattr(theme.spacing, s)
                    for s in ("xs","sm","md","lg","xl","xxl")},
        "button": {
            "normal":        _surf(theme.button.normal),
            "hovered":       _surf(theme.button.hovered),
            "pressed":       _surf(theme.button.pressed),
            "disabled":      _surf(theme.button.disabled),
            "text":          _text(theme.button.text),
            "text_disabled": _text(theme.button.text_disabled),
            "padding":       theme.button.padding,
        },
        "label": {
            "text":           _text(theme.label.text),
            "secondary_text": _text(theme.label.secondary_text),
        },
        "panel": {
            "surface": _surf(theme.panel.surface),
            "padding": theme.panel.padding,
        },
    }
