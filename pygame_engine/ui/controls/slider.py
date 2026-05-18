"""
A horizontal or vertical slider for selecting a value in a continuous range.
Reads visual style from the active theme.

Usage::

    from pygame_engine.ui.controls.slider import Slider

    vol = Slider(
        rect=pygame.Rect(100, 200, 220, 24),
        value=0.8,
        on_change=lambda v: app.audio.set_master_volume(v),
    )
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget
from pygame_engine.utils.mathx import clamp


class Slider(Widget):
    """
    Horizontal slider for a float value in [min_value, max_value].

    The user can drag the thumb or click anywhere on the track to jump to
    that position. Keyboard: Left/Right (or Down/Up for vertical) move the
    thumb by ``step``; Home/End jump to min/max.

    Args:
        rect:       Position and size. Width should be much greater than
                    height for horizontal sliders (recommend height=20–28).
        value:      Initial value. Clamped to [min_value, max_value].
        min_value:  Minimum of the range. Default 0.0.
        max_value:  Maximum of the range. Default 1.0.
        step:       Keyboard step size. Default 0.05 (5% of range).
        vertical:   If True, the slider is vertical (value increases upward).
        on_change:  Called with the new float value whenever it changes.
    """

    THUMB_W = 14    # thumb width  (pixels)
    THUMB_H = 24    # thumb height (pixels, may exceed rect height)

    def __init__(
        self,
        rect:       pygame.Rect,
        value:      float = 0.5,
        min_value:  float = 0.0,
        max_value:  float = 1.0,
        step:       float = 0.05,
        vertical:   bool  = False,
        on_change:  Callable[[float], None] | None = None,
    ) -> None:
        super().__init__(rect)
        self.min_value  = min_value
        self.max_value  = max_value
        self.step       = step
        self.vertical   = vertical
        self.on_change  = on_change
        self.focusable  = True

        self._dragging  = False
        self._value     = clamp(value, min_value, max_value)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def value(self) -> float:
        """Return the current slider value."""
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        """Return the current slider value."""
        clamped = clamp(v, self.min_value, self.max_value)
        if clamped != self._value:
            self._value = clamped
            if self.on_change:
                self.on_change(self._value)

    @property
    def normalised(self) -> float:
        """Value normalised to [0.0, 1.0]."""
        span = self.max_value - self.min_value
        if span == 0:
            return 0.0
        return (self._value - self.min_value) / span

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._set_from_mouse(event.pos)
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True

        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_from_mouse(event.pos)
            return True

        if event.type == pygame.KEYDOWN and self.focused:
            dec_keys = (pygame.K_LEFT, pygame.K_DOWN) if not self.vertical else (pygame.K_DOWN,)
            inc_keys = (pygame.K_RIGHT, pygame.K_UP)  if not self.vertical else (pygame.K_UP,)
            if event.key in dec_keys:
                self.value = self._value - self.step
                return True
            if event.key in inc_keys:
                self.value = self._value + self.step
                return True
            if event.key == pygame.K_HOME:
                self.value = self.min_value
                return True
            if event.key == pygame.K_END:
                self.value = self.max_value
                return True

        return False

    def _set_from_mouse(self, pos: tuple[int, int]) -> None:
        half_thumb = self.THUMB_W // 2
        if self.vertical:
            track_len = self.rect.height - self.THUMB_W
            raw = self.rect.bottom - half_thumb - pos[1]
        else:
            track_len = self.rect.width - self.THUMB_W
            raw = pos[0] - self.rect.x - half_thumb

        if track_len <= 0:
            return
        t = clamp(raw / track_len, 0.0, 1.0)
        self.value = self.min_value + t * (self.max_value - self.min_value)

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the slider onto surface."""
        if not self.visible:
            return

        theme  = get_theme()
        colours = theme.colours

        # Track
        track_rect = self._track_rect()
        pygame.draw.rect(surface, colours.bg_raised, track_rect,
                         border_radius=track_rect.height // 2)
        pygame.draw.rect(surface, colours.border, track_rect, width=1,
                         border_radius=track_rect.height // 2)

        # Filled portion
        fill = self._fill_rect(track_rect)
        if fill.width > 0 and fill.height > 0:
            pygame.draw.rect(surface, theme.button.normal.bg, fill,
                             border_radius=track_rect.height // 2)

        # Thumb
        thumb = self._thumb_rect()
        pygame.draw.rect(surface, theme.button.hovered.bg if self.hovered or self._dragging
                         else theme.button.normal.bg,
                         thumb, border_radius=4)
        pygame.draw.rect(surface, theme.button.hovered.border if self.focused
                         else colours.border,
                         thumb, width=1, border_radius=4)

        # Focus ring
        if self.focused and self.enabled:
            pygame.draw.rect(surface, colours.border_focus,
                             thumb.inflate(4, 4), width=2, border_radius=6)

    # ── Geometry helpers ──────────────────────────────────────────────────────

    def _track_rect(self) -> pygame.Rect:
        if self.vertical:
            cx = self.rect.centerx
            return pygame.Rect(cx - 3, self.rect.y + self.THUMB_W // 2,
                               6, self.rect.height - self.THUMB_W)
        cy = self.rect.centery
        return pygame.Rect(self.rect.x + self.THUMB_W // 2, cy - 3,
                           self.rect.width - self.THUMB_W, 6)

    def _fill_rect(self, track: pygame.Rect) -> pygame.Rect:
        n = self.normalised
        if self.vertical:
            h = int(track.height * n)
            return pygame.Rect(track.x, track.bottom - h, track.width, h)
        return pygame.Rect(track.x, track.y, int(track.width * n), track.height)

    def _thumb_rect(self) -> pygame.Rect:
        n = self.normalised
        if self.vertical:
            track_len = self.rect.height - self.THUMB_W
            cy = int(self.rect.bottom - self.THUMB_W // 2 - n * track_len)
            cx = self.rect.centerx
            return pygame.Rect(cx - self.THUMB_W // 2, cy - self.THUMB_H // 2,
                               self.THUMB_W, self.THUMB_H)
        track_len = self.rect.width - self.THUMB_W
        cx = int(self.rect.x + self.THUMB_W // 2 + n * track_len)
        cy = self.rect.centery
        return pygame.Rect(cx - self.THUMB_W // 2, cy - self.THUMB_H // 2,
                           self.THUMB_W, self.THUMB_H)