"""
The universal pattern for presenting structured data: a left column of
muted labels, a right column of primary values. Used in hero detail panels,
item inspectors, settings summaries, and stat displays.

Usage::

    from pygame_engine.ui.controls.key_value_panel import KeyValuePanel

    kv = KeyValuePanel(
        rect=pygame.Rect(40, 400, 500, 300),
        rows=[
            ("Name",       hero.name),
            ("Class",      hero.hero_class),
            ("Level",      hero.level),
            ("Power",      hero.combat_power()),
            ("Satisfaction", f"{hero.satisfaction}/100"),
        ],
    )
    kv.render(surface)

    # Update rows at any time:
    kv.set_rows([("Gold", f"{state.gold}g"), ...])
"""

from __future__ import annotations

import pygame

from pygame_engine.graphics.draw_utils import draw_rect_bordered
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class KeyValuePanel(Widget):
    """
    Two-column label/value display panel.

    Draws a styled background panel, then renders pairs of text with the
    label column left-aligned in a muted colour and the value column
    right-aligned (or at a fixed split point) in the primary text colour.

    Args:
        rect:          Widget rect.
        rows:          List of ``(label, value)`` pairs. Values are converted
                       to str automatically.
        split:         X offset from the left edge where values start.
                       None = auto (half the inner width).
        row_height:    Pixels per row. None = derived from font size.
        padding:       Inner padding from panel edge to content.
        font_size:     Override font size. None = theme ``sm``.
        label_colour:  Override label colour. None = theme secondary text.
        value_colour:  Override value colour. None = theme primary text.
        title:         Optional title string drawn above the rows.
    """

    def __init__(
        self,
        rect:          pygame.Rect,
        rows:          list[tuple[str, object]] | None = None,
        split:         int | None = None,
        row_height:    int | None = None,
        padding:       int = 12,
        font_size:     int | None = None,
        label_colour:  tuple[int, int, int] | None = None,
        value_colour:  tuple[int, int, int] | None = None,
        title:         str = "",
    ) -> None:
        super().__init__(rect)
        self._rows:         list[tuple[str, str]] = []
        self._split:        int | None = split
        self._row_height:   int | None = row_height
        self._padding:      int   = padding
        self._font_size:    int | None = font_size
        self._label_colour: tuple | None = label_colour
        self._value_colour: tuple | None = value_colour
        self.title          = title

        if rows:
            self.set_rows(rows)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_rows(self, rows: list[tuple[str, object]]) -> None:
        """Replace all rows. Values are converted to str."""
        self._rows = [(str(label), str(value)) for label, value in rows]

    def append_row(self, label: str, value: object) -> None:
        """Add a single row."""
        self._rows.append((label, str(value)))

    def clear(self) -> None:
        """Remove all rows from the panel."""
        self._rows = []

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the panel rect."""
        self.rect = rect

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the key-value panel onto surface."""
        if not self.visible:
            return

        theme = get_theme()

        draw_rect_bordered(
            surface, self.rect,
            fill=theme.colours.bg_base,
            border=theme.colours.border,
            radius=theme.panel.surface.radius,
        )

        font_size   = self._font_size or theme.typography.sm
        font        = pygame.font.SysFont(theme.typography.family, font_size)
        label_col   = self._label_colour or theme.colours.text_secondary
        value_col   = self._value_colour or theme.colours.text
        row_h       = self._row_height or (font.get_linesize() + 6)
        pad         = self._padding
        inner_w     = self.rect.width - pad * 2

        y = self.rect.y + pad

        # Optional title
        if self.title:
            title_font = pygame.font.SysFont(
                theme.typography.family, theme.typography.md, bold=True)
            tsurf = title_font.render(self.title, True, theme.colours.text)
            surface.blit(tsurf, (self.rect.x + pad, y))
            y += title_font.get_linesize() + pad

        # Auto-compute split if not given
        split = self._split
        if split is None:
            # Widest label + 16px gap
            if self._rows:
                split = max(font.size(lbl)[0] for lbl, _ in self._rows) + 16
            else:
                split = inner_w // 2

        lx = self.rect.x + pad
        vx = lx + split

        for label, value in self._rows:
            if y + row_h > self.rect.bottom:
                break
            cy = y + row_h // 2

            lsurf = font.render(label, True, label_col)
            surface.blit(lsurf, (lx, cy - lsurf.get_height() // 2))

            vsurf = font.render(value, True, value_col)
            surface.blit(vsurf, (vx, cy - vsurf.get_height() // 2))

            y += row_h