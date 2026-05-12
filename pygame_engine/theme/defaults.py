"""
theme/defaults.py

The engine's default theme, built from design tokens.

Defines a hierarchy of dataclasses that cover every widget type in
pygame_engine. Widgets look up their style through the runtime theme;
this file is the source of those default values.

Structure
---------
  Theme
  ├── colours       (background, text, border palettes for scenes/surfaces)
  ├── typography    (font family, sizes by role)
  ├── spacing       (standard padding/gap values)
  ├── button        (ButtonTheme — normal/hover/pressed/disabled states)
  ├── label         (LabelTheme — text defaults)
  ├── panel         (PanelTheme — surface background/border)
  └── (future: tooltip, toast, input, dropdown, scrollbar …)

The root ``Theme`` dataclass is instantiated as ``DEFAULT_THEME`` at the
bottom of this file. ``runtime.py`` uses it as the fallback when no
project-level theme is set.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame_engine.theme.tokens import Borders, Colours, Radii, Spacing, Typography


# ── Widget state style atoms ──────────────────────────────────────────────────

@dataclass
class SurfaceStyle:
    """Background colour, border colour, border width, and corner radius."""
    bg:           tuple[int, int, int] = field(default_factory=lambda: Colours.SURFACE_0)
    border:       tuple[int, int, int] = field(default_factory=lambda: Colours.BORDER_DEFAULT)
    border_width: int                  = Borders.THIN
    radius:       int                  = Radii.MD


@dataclass
class TextStyle:
    """Text colour, font size, and font family."""
    colour:      tuple[int, int, int] = field(default_factory=lambda: Colours.TEXT_PRIMARY)
    font_size:   int                  = Typography.SIZE_MD
    font_family: str                  = Typography.FONT_FAMILY
    bold:        bool                 = False


# ── Per-widget themes ─────────────────────────────────────────────────────────

@dataclass
class ButtonTheme:
    """Visual style for each interactive state of a Button."""
    normal:   SurfaceStyle = field(default_factory=lambda: SurfaceStyle(
        bg=Colours.PRIMARY, border=Colours.BORDER_DEFAULT,
        border_width=Borders.THIN, radius=Radii.MD,
    ))
    hovered:  SurfaceStyle = field(default_factory=lambda: SurfaceStyle(
        bg=Colours.PRIMARY_LIGHT, border=Colours.BORDER_FOCUS,
        border_width=Borders.THIN, radius=Radii.MD,
    ))
    pressed:  SurfaceStyle = field(default_factory=lambda: SurfaceStyle(
        bg=Colours.PRIMARY_DARK, border=Colours.BORDER_DEFAULT,
        border_width=Borders.THIN, radius=Radii.MD,
    ))
    disabled: SurfaceStyle = field(default_factory=lambda: SurfaceStyle(
        bg=Colours.DISABLED_BG, border=Colours.BORDER_SUBTLE,
        border_width=Borders.THIN, radius=Radii.MD,
    ))
    text:          TextStyle = field(default_factory=lambda: TextStyle(
        colour=Colours.TEXT_PRIMARY, font_size=Typography.SIZE_MD,
    ))
    text_disabled: TextStyle = field(default_factory=lambda: TextStyle(
        colour=Colours.TEXT_DISABLED, font_size=Typography.SIZE_MD,
    ))
    padding: int = Spacing.SM


@dataclass
class LabelTheme:
    """Default style for a Label widget."""
    text: TextStyle = field(default_factory=lambda: TextStyle(
        colour=Colours.TEXT_PRIMARY, font_size=Typography.SIZE_MD,
    ))
    secondary_text: TextStyle = field(default_factory=lambda: TextStyle(
        colour=Colours.TEXT_SECONDARY, font_size=Typography.SIZE_SM,
    ))


@dataclass
class PanelTheme:
    """Default style for a Panel container widget."""
    surface:  SurfaceStyle = field(default_factory=lambda: SurfaceStyle(
        bg=Colours.SURFACE_0, border=Colours.BORDER_SUBTLE,
        border_width=Borders.THIN, radius=Radii.MD,
    ))
    padding: int = Spacing.MD


# ── Shared scene/global theme values ─────────────────────────────────────────

@dataclass
class ColoursTheme:
    """Global colour roles used by scenes and non-widget drawing."""
    bg_dark:    tuple[int, int, int] = field(default_factory=lambda: Colours.BG_DARK)
    bg_base:    tuple[int, int, int] = field(default_factory=lambda: Colours.BG_BASE)
    bg_raised:  tuple[int, int, int] = field(default_factory=lambda: Colours.BG_RAISED)
    text:       tuple[int, int, int] = field(default_factory=lambda: Colours.TEXT_PRIMARY)
    text_secondary: tuple[int, int, int] = field(default_factory=lambda: Colours.TEXT_SECONDARY)
    border:     tuple[int, int, int] = field(default_factory=lambda: Colours.BORDER_DEFAULT)


@dataclass
class TypographyTheme:
    """Font family and sizes used across the engine."""
    family:  str = Typography.FONT_FAMILY
    xs:      int = Typography.SIZE_XS
    sm:      int = Typography.SIZE_SM
    md:      int = Typography.SIZE_MD
    lg:      int = Typography.SIZE_LG
    xl:      int = Typography.SIZE_XL
    xxl:     int = Typography.SIZE_XXL


@dataclass
class SpacingTheme:
    """Standard spacing values."""
    xs:  int = Spacing.XS
    sm:  int = Spacing.SM
    md:  int = Spacing.MD
    lg:  int = Spacing.LG
    xl:  int = Spacing.XL
    xxl: int = Spacing.XXL


# ── Root Theme dataclass ──────────────────────────────────────────────────────

@dataclass
class Theme:
    """
    Root theme object.

    Access via ``runtime.get_theme()``::

        from pygame_engine.theme.runtime import get_theme

        theme = get_theme()
        surface_colour = theme.colours.bg_base
        btn_bg = theme.button.normal.bg
        font_size = theme.typography.md
    """
    colours:    ColoursTheme    = field(default_factory=ColoursTheme)
    typography: TypographyTheme = field(default_factory=TypographyTheme)
    spacing:    SpacingTheme    = field(default_factory=SpacingTheme)
    button:     ButtonTheme     = field(default_factory=ButtonTheme)
    label:      LabelTheme      = field(default_factory=LabelTheme)
    panel:      PanelTheme      = field(default_factory=PanelTheme)


# ── Engine default instance ───────────────────────────────────────────────────

DEFAULT_THEME: Theme = Theme()
