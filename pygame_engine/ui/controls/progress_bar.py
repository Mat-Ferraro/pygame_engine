"""
ProgressBar widget for pygame_engine.

Displays a filled bar representing a ratio from 0.0 to 1.0.
Useful for health bars, loading screens, XP bars, volume sliders,
cooldown indicators — anything that shows progress or a proportion.

The bar can be horizontal (default) or vertical. Fill direction is
always from the "start" edge (left for horizontal, bottom for vertical).

Styling comes from the active theme with optional per-instance overrides.
The fill colour can be set directly or driven by a Tween for smooth
transitions.

Usage::

    from pygame_engine.ui.controls.progress_bar import ProgressBar

    # Simple health bar
    hp_bar = ProgressBar(pygame.Rect(100, 50, 200, 20), value=0.8)

    # Each frame — update value, widget handles rendering
    hp_bar.value = player.hp / player.max_hp
    hp_bar.render(surface)

    # Vertical bar (fills bottom-up)
    mana_bar = ProgressBar(
        pygame.Rect(20, 100, 16, 120),
        value=0.5,
        direction="vertical",
        fill_colour=(80, 120, 220),
    )
"""

from __future__ import annotations

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class ProgressBar(Widget):
    """
    Filled bar widget showing a normalised value (0.0 – 1.0).

    Direction
    ---------
    ``"horizontal"`` — fills left to right (default).
    ``"vertical"``   — fills bottom to top.

    Styling
    -------
    ``fill_colour`` and ``bg_colour`` can be passed at construction to
    override the theme defaults. Pass ``None`` to use theme values.

    Smooth transitions
    ------------------
    Drive ``value`` from a ``Tween`` each frame for animated bars::

        self._hp_tween.update(dt)
        hp_bar.value = self._hp_tween.value
    """

    def __init__(
        self,
        rect:         pygame.Rect,
        value:        float = 1.0,
        direction:    str   = "horizontal",
        fill_colour:  tuple[int, int, int] | None = None,
        bg_colour:    tuple[int, int, int] | None = None,
        border_radius: int | None = None,
    ) -> None:
        """
        Args:
            rect:          Position and size of the bar.
            value:         Initial fill ratio in [0.0, 1.0].
            direction:     ``"horizontal"`` or ``"vertical"``.
            fill_colour:   Fill colour override. None = use theme accent.
            bg_colour:     Background colour override. None = use theme.
            border_radius: Corner radius override. None = use theme.
        """
        super().__init__(rect)

        self._value:         float = max(0.0, min(1.0, value))
        self._direction:     str   = direction
        self._fill_colour:   tuple[int, int, int] | None = fill_colour
        self._bg_colour:     tuple[int, int, int] | None = bg_colour
        self._border_radius: int | None = border_radius

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def value(self) -> float:
        """Current fill ratio in [0.0, 1.0]."""
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        """Return the current fill value in the range 0.0–1.0."""
        self._value = max(0.0, min(1.0, v))

    @property
    def direction(self) -> str:
        """Return the fill direction ('horizontal' or 'vertical')."""
        return self._direction

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the progress bar onto surface."""
        if not self.visible:
            return

        theme  = get_theme()
        radius = (self._border_radius
                  if self._border_radius is not None
                  else theme.panel.surface.radius)
        bg     = self._bg_colour or theme.colours.bg_raised
        fill   = self._fill_colour or theme.colours.text  # sensible fallback

        # Background track
        pygame.draw.rect(surface, bg, self.rect, border_radius=radius)

        # Fill rect
        fill_rect = self._compute_fill_rect()
        if fill_rect.width > 0 and fill_rect.height > 0:
            pygame.draw.rect(surface, fill, fill_rect,
                             border_radius=radius)

        # Border
        border = theme.panel.surface.border
        bw     = theme.panel.surface.border_width
        if bw > 0:
            pygame.draw.rect(surface, border, self.rect,
                             width=bw, border_radius=radius)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _compute_fill_rect(self) -> pygame.Rect:
        """Return the rect representing the filled portion."""
        if self._direction == "vertical":
            fill_h = int(self.rect.height * self._value)
            return pygame.Rect(
                self.rect.x,
                self.rect.bottom - fill_h,
                self.rect.width,
                fill_h,
            )
        else:  # horizontal
            fill_w = int(self.rect.width * self._value)
            return pygame.Rect(
                self.rect.x,
                self.rect.y,
                fill_w,
                self.rect.height,
            )