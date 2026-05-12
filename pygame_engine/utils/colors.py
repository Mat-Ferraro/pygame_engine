"""
utils/colors.py

Low-level colour helpers for pygame_engine.

These are generic math/conversion utilities. Actual visual identity
values (brand colours, widget colours) belong in theme/tokens.py, not
here.

All colours are represented as RGB tuples of ints unless noted.
"""

from __future__ import annotations

import math


Color = tuple[int, int, int]
ColorA = tuple[int, int, int, int]


# ── Interpolation ─────────────────────────────────────────────────────────────

def lerp_color(
    a: Color,
    b: Color,
    t: float,
) -> Color:
    """
    Linearly interpolate between two RGB colours.

    Args:
        a: Start colour.
        b: End colour.
        t: Blend factor from 0.0 (a) to 1.0 (b). Clamped.

    Returns:
        Blended RGB colour.
    """
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def lerp_color_alpha(
    a: ColorA,
    b: ColorA,
    t: float,
) -> ColorA:
    """
    Linearly interpolate between two RGBA colours.

    Args:
        a: Start colour (R, G, B, A).
        b: End colour (R, G, B, A).
        t: Blend factor 0.0–1.0. Clamped.

    Returns:
        Blended RGBA colour.
    """
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
        int(a[3] + (b[3] - a[3]) * t),
    )


# ── Brightness / manipulation ─────────────────────────────────────────────────

def brighten(color: Color, factor: float) -> Color:
    """
    Multiply each channel by ``factor`` and clamp to 0–255.

    Args:
        color:  Source RGB colour.
        factor: Multiplier. > 1.0 brightens; < 1.0 darkens.

    Returns:
        Adjusted RGB colour.
    """
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def with_alpha(color: Color, alpha: int) -> ColorA:
    """
    Add an alpha channel to an RGB colour.

    Args:
        color: Source RGB colour.
        alpha: Alpha value 0–255.

    Returns:
        RGBA colour tuple.
    """
    return (color[0], color[1], color[2], max(0, min(255, alpha)))


# ── Conversion ────────────────────────────────────────────────────────────────

def hex_to_rgb(hex_str: str) -> Color:
    """
    Convert a hex colour string to an RGB tuple.

    Args:
        hex_str: Hex colour string, with or without leading ``#``.
                 Supports 6-digit (``#RRGGBB``) and 3-digit (``#RGB``)
                 formats.

    Returns:
        RGB tuple with values 0–255.

    Raises:
        ValueError: If the string is not a valid hex colour.
    """
    s = hex_str.lstrip("#")
    if len(s) == 3:
        s = s[0] * 2 + s[1] * 2 + s[2] * 2
    if len(s) != 6:
        raise ValueError(f"Invalid hex colour: {hex_str!r}")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return (r, g, b)


def rgb_to_hex(color: Color) -> str:
    """
    Convert an RGB tuple to a ``#RRGGBB`` hex string.

    Args:
        color: RGB tuple with values 0–255.

    Returns:
        Hex string in the form ``"#rrggbb"``.
    """
    return "#{:02x}{:02x}{:02x}".format(*color)


def hsv_to_rgb(h: float, s: float, v: float) -> Color:
    """
    Convert HSV colour to an RGB tuple.

    Args:
        h: Hue, 0.0–1.0.
        s: Saturation, 0.0–1.0.
        v: Value (brightness), 0.0–1.0.

    Returns:
        RGB tuple with values 0–255.
    """
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))
