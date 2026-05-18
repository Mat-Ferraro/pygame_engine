"""
Raw design tokens for pygame_engine.

Tokens are the smallest named design values — the atoms of the theme
system. They are reusable, generic, and stable. Widgets and defaults
reference tokens rather than hardcoding magic numbers.

Tokens are plain constants. They do not carry logic or state.

Structure
---------
- Colours   — base palette
- Spacing   — standard gap/padding values
- Typography — font sizes and families
- Radii     — corner radius values
- Borders   — border width values
- Timing    — standard UI animation durations
"""

from __future__ import annotations

# ── Colour palette ────────────────────────────────────────────────────────────
# Named by role/shade, not by widget. Widgets reference these through defaults.

class Colours:
    """Theme colour palette — backgrounds, foregrounds, and accent colours."""
    # Dark backgrounds
    BG_DARK      = (15,  15,  20)
    BG_BASE      = (22,  22,  30)
    BG_RAISED    = (30,  30,  42)
    BG_OVERLAY   = (38,  38,  54)

    # Surfaces (widget backgrounds)
    SURFACE_0    = (40,  44,  60)    # default widget surface
    SURFACE_1    = (52,  58,  78)    # raised surface
    SURFACE_2    = (64,  72,  96)    # further raised

    # Primary accent (blue)
    PRIMARY_DARK  = (35,  60,  130)
    PRIMARY       = (55,  90,  180)
    PRIMARY_LIGHT = (80,  120, 215)
    PRIMARY_PALE  = (110, 150, 230)

    # Semantic colours
    SUCCESS  = (60,  170, 100)
    WARNING  = (210, 150, 40)
    ERROR    = (200, 70,  60)
    INFO     = (60,  160, 210)

    # Text
    TEXT_PRIMARY   = (225, 225, 232)
    TEXT_SECONDARY = (160, 160, 175)
    TEXT_DISABLED  = (100, 100, 115)
    TEXT_INVERSE   = (15,  15,  20)

    # Borders
    BORDER_SUBTLE  = (55,  60,  80)
    BORDER_DEFAULT = (80,  90,  120)
    BORDER_FOCUS   = (100, 140, 220)

    # Disabled state
    DISABLED_BG   = (45,  45,  55)
    DISABLED_FG   = (90,  90,  105)


# ── Spacing scale (pixels) ────────────────────────────────────────────────────

class Spacing:
    """Theme spacing values — padding, gaps, and margins in pixels."""
    XS  = 4
    SM  = 8
    MD  = 12
    LG  = 16
    XL  = 24
    XXL = 32


# ── Typography ────────────────────────────────────────────────────────────────

class Typography:
    """Theme typography settings — font family and size scale."""
    FONT_FAMILY = "segoeui,helvetica,arial"

    SIZE_XS  = 12
    SIZE_SM  = 14
    SIZE_MD  = 18
    SIZE_LG  = 22
    SIZE_XL  = 28
    SIZE_XXL = 36


# ── Radii (border-radius values in pixels) ────────────────────────────────────

class Radii:
    """Theme border radius values in pixels."""
    NONE   = 0
    SM     = 3
    MD     = 6
    LG     = 10
    FULL   = 999   # pill shape — use with caution


# ── Border widths ─────────────────────────────────────────────────────────────

class Borders:
    """Theme border width values in pixels."""
    NONE   = 0
    THIN   = 1
    MEDIUM = 2
    THICK  = 3


# ── Timing (milliseconds) ─────────────────────────────────────────────────────

class Timing:
    """Theme animation timing values in seconds."""
    INSTANT  = 0
    FAST     = 80
    NORMAL   = 150
    SLOW     = 300
    VERY_SLOW = 500