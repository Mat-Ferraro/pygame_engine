"""
Used anywhere a bounded integer needs to be adjusted by hand: contract
campaign count, team size, difficulty, volume level, etc.

Usage::

    from pygame_engine.ui.controls.int_stepper import IntStepper

    stepper = IntStepper(
        rect=pygame.Rect(300, 400, 200, 48),
        value=1,
        min_value=1,
        max_value=8,
        label="Campaigns",
        on_change=lambda v: self.set_campaigns(v),
    )
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.graphics.draw_utils import draw_rect_bordered, draw_chevron
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class IntStepper(Widget):
    """
    Horizontal stepper: [−]  value  [+] with an optional title label above.

    The − and + buttons are inset at the left and right edges of the rect.
    The current value is displayed centred between them.

    Keyboard (when focused): Left/Right to decrement/increment.

    Args:
        rect:       Full widget rect (includes buttons, value, and title).
        value:      Initial integer value.
        min_value:  Minimum allowed value (inclusive).
        max_value:  Maximum allowed value (inclusive).
        step:       How much each button press changes the value.
        label:      Optional title text drawn above the control.
        fmt:        Format string applied to the value. Default ``"{v}"``.
                    Use e.g. ``"{v}g"`` to suffix a unit.
        on_change:  Called with the new int value whenever it changes.
    """

    BTN_W = 36   # width of each − / + button

    def __init__(
        self,
        rect:       pygame.Rect,
        value:      int = 0,
        min_value:  int = 0,
        max_value:  int = 100,
        step:       int = 1,
        label:      str = "",
        fmt:        str = "{v}",
        on_change:  Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(rect)
        self.min_value = min_value
        self.max_value = max_value
        self.step      = step
        self.label     = label
        self.fmt       = fmt
        self.on_change = on_change
        self.focusable = True

        self._value         = max(min_value, min(max_value, value))
        self._dec_pressed   = False
        self._inc_pressed   = False

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def value(self) -> int:
        """Return the current stepper value."""
        return self._value

    @value.setter
    def value(self, v: int) -> None:
        """Return the current stepper value."""
        clamped = max(self.min_value, min(self.max_value, v))
        if clamped != self._value:
            self._value = clamped
            if self.on_change:
                self.on_change(self._value)

    def increment(self) -> None:
        """Increase the value by one step, clamped to maximum."""
        self.value = self._value + self.step

    def decrement(self) -> None:
        """Decrease the value by one step, clamped to minimum."""
        self.value = self._value - self.step

    # ── Events ────────────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        dec_rect, inc_rect = self._btn_rects()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if dec_rect.collidepoint(event.pos):
                self._dec_pressed = True
                return True
            if inc_rect.collidepoint(event.pos):
                self._inc_pressed = True
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dec_pressed:
                self._dec_pressed = False
                if dec_rect.collidepoint(event.pos):
                    self.decrement()
                return True
            if self._inc_pressed:
                self._inc_pressed = False
                if inc_rect.collidepoint(event.pos):
                    self.increment()
                return True

        if event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_LEFT, pygame.K_DOWN):
                self.decrement()
                return True
            if event.key in (pygame.K_RIGHT, pygame.K_UP):
                self.increment()
                return True

        return False

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the stepper onto surface."""
        if not self.visible:
            return

        theme     = get_theme()
        dec_r, inc_r = self._btn_rects()
        val_r        = self._value_rect()

        # Optional title
        if self.label:
            font_sm = pygame.font.SysFont(theme.typography.family,
                                          theme.typography.sm)
            lsurf = font_sm.render(self.label, True, theme.colours.text_secondary)
            surface.blit(lsurf, (self.rect.x, self.rect.y))

        # Value background
        draw_rect_bordered(
            surface, val_r,
            fill=theme.colours.bg_raised,
            border=theme.colours.border,
            radius=4,
        )

        # Value text
        font_md = pygame.font.SysFont(theme.typography.family,
                                      theme.typography.md)
        vtext = self.fmt.format(v=self._value)
        vsurf = font_md.render(vtext, True, theme.colours.text)
        surface.blit(vsurf, vsurf.get_rect(center=val_r.center))

        # Dec button
        at_min = self._value <= self.min_value
        self._draw_btn(surface, dec_r, self._dec_pressed, at_min, theme)
        cx, cy = dec_r.center
        draw_chevron(surface, (cx, cy), 5, theme.colours.text_secondary
                     if not at_min else theme.colours.border,
                     direction="left", width=2)

        # Inc button
        at_max = self._value >= self.max_value
        self._draw_btn(surface, inc_r, self._inc_pressed, at_max, theme)
        cx, cy = inc_r.center
        draw_chevron(surface, (cx, cy), 5, theme.colours.text_secondary
                     if not at_max else theme.colours.border,
                     direction="right", width=2)

        # Focus ring
        if self.focused and self.enabled:
            pygame.draw.rect(surface, theme.colours.border,
                             self.rect.inflate(4, 4), width=2, border_radius=6)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _control_rect(self) -> pygame.Rect:
        """Bottom portion of rect used for the actual stepper control."""
        if self.label:
            theme    = get_theme()
            title_h  = theme.typography.sm + 4
            return pygame.Rect(
                self.rect.x,
                self.rect.y + title_h,
                self.rect.width,
                self.rect.height - title_h,
            )
        return pygame.Rect(self.rect)

    def _btn_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        cr = self._control_rect()
        dec = pygame.Rect(cr.x,              cr.y, self.BTN_W, cr.height)
        inc = pygame.Rect(cr.right - self.BTN_W, cr.y, self.BTN_W, cr.height)
        return dec, inc

    def _value_rect(self) -> pygame.Rect:
        cr  = self._control_rect()
        return pygame.Rect(
            cr.x + self.BTN_W,
            cr.y,
            cr.width - self.BTN_W * 2,
            cr.height,
        )

    def _draw_btn(self, surface, rect, pressed, disabled, theme) -> None:
        if disabled:
            bg = theme.button.disabled.bg
        elif pressed:
            bg = theme.button.pressed.bg
        else:
            bg = theme.button.normal.bg
        border = theme.colours.border
        draw_rect_bordered(surface, rect, fill=bg, border=border, radius=4)