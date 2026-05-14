"""
Badge — small coloured pill label with semantic styles.

A Badge is a compact, non-interactive status indicator that communicates
a category, state, or count at a glance. Common uses: hero class labels,
status indicators (Injured, Expiring, Ready), item rarity, tier markers.

Usage::

    from pygame_engine.ui.controls.badge import Badge

    b = Badge(pygame.Rect(x, y, 80, 24), "Warrior", style="info")
    b.render(surface)

    # Style options:
    #   "default"  — neutral grey
    #   "info"     — blue
    #   "good"     — green
    #   "warning"  — amber
    #   "danger"   — red
"""

from __future__ import annotations

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


# Semantic colour palettes: (bg, border, text)
_STYLES: dict[str, tuple[tuple, tuple, tuple]] = {
    "default": ((55,  55,  68),  (90,  90, 110),  (200, 200, 212)),
    "info":    ((30,  60, 110),  (60, 100, 175),   (160, 200, 255)),
    "good":    ((30,  75,  40),  (55, 130,  70),   (140, 230, 155)),
    "warning": ((90,  65,  15),  (170, 120,  30),  (240, 195,  90)),
    "danger":  ((100, 28,  28),  (180,  60,  60),  (255, 145, 145)),
}


class Badge(Widget):
    """
    Small coloured pill label with a semantic style.

    Does not handle events. Size is fixed to the supplied rect — the badge
    does not auto-resize to fit its text. Keep labels short (1–15 chars).

    Args:
        rect:       Position and size. Recommended height: 22–28 px.
        text:       Label to display inside the badge.
        style:      One of ``"default"``, ``"info"``, ``"good"``,
                    ``"warning"``, ``"danger"``.
        font_size:  Override font size. None = theme ``sm``.
    """

    def __init__(
        self,
        rect:      pygame.Rect,
        text:      str = "",
        style:     str = "default",
        font_size: int | None = None,
    ) -> None:
        super().__init__(rect)
        self._text      = text
        self._style     = style
        self._font_size = font_size
        self._font:   pygame.font.Font | None = None
        self._surf:   pygame.Surface | None   = None
        self._dirty:  bool = True

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text  = value
            self._dirty = True

    @property
    def style(self) -> str:
        return self._style

    @style.setter
    def style(self, value: str) -> None:
        if value != self._style:
            self._style = value
            self._dirty = True

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect   = rect
        self._dirty = True

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if self._dirty:
            self._rebuild()
        if self._surf is not None:
            surface.blit(self._surf, self.rect.topleft)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        theme      = get_theme()
        font_size  = self._font_size or theme.typography.sm
        self._font = pygame.font.SysFont(theme.typography.family, font_size)

        bg, border, text_col = _STYLES.get(self._style, _STYLES["default"])

        self._surf = pygame.Surface(
            (self.rect.width, self.rect.height), pygame.SRCALPHA
        )
        radius = self.rect.height // 2   # pill shape
        pygame.draw.rect(self._surf, (*bg, 220),
                         pygame.Rect(0, 0, self.rect.width, self.rect.height),
                         border_radius=radius)
        pygame.draw.rect(self._surf, (*border, 200),
                         pygame.Rect(0, 0, self.rect.width, self.rect.height),
                         width=1, border_radius=radius)

        text_surf = self._font.render(self._text, True, text_col)
        tx = (self.rect.width  - text_surf.get_width())  // 2
        ty = (self.rect.height - text_surf.get_height()) // 2
        self._surf.blit(text_surf, (tx, ty))

        self._dirty = False
