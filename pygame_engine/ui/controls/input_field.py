"""
Supports typing, cursor movement, backspace, placeholder text, and
focus management. Uses pygame's TEXTINPUT event system for correct
Unicode and IME handling.

v1 scope: typing, backspace, cursor movement (arrows, Home, End),
click-to-focus, placeholder, on_change/on_submit callbacks.

Deferred: selection, cut/copy/paste, Ctrl+Backspace, undo.

Usage::

    from pygame_engine.ui.controls.input_field import InputField

    field = InputField(
        rect=pygame.Rect(100, 200, 300, 42),
        placeholder="Enter your name...",
        on_submit=lambda text: start_game(text),
    )

    # In handle_event:
    field.handle_event(event)

    # In update:
    field.update(dt)

    # In render:
    field.render(surface)

    # Read the current value:
    name = field.text
"""

from __future__ import annotations

import math
from typing import Callable

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class InputField(Widget):
    """
    Single-line text input widget.

    Focus
    -----
    Click inside to focus. Click outside (handled by the scene or
    container) to unfocus. When focused, pygame text input events are
    active and the cursor blinks.

    Callbacks
    ---------
    ``on_change(text)`` — called on every character change.
    ``on_submit(text)`` — called when Enter is pressed.

    Both receive the current text string. Either may be None.
    """

    CURSOR_BLINK_RATE = 0.53   # seconds per blink half-cycle

    def __init__(
        self,
        rect:        pygame.Rect,
        text:        str = "",
        placeholder: str = "",
        max_length:  int | None = None,
        on_change:   Callable[[str], None] | None = None,
        on_submit:   Callable[[str], None] | None = None,
        password:    bool = False,
    ) -> None:
        """
        Args:
            rect:        Position and size of the input field.
            text:        Initial text value.
            placeholder: Ghost text shown when the field is empty and
                         unfocused.
            max_length:  Maximum number of characters. None = unlimited.
            on_change:   Called with the new text on every change.
            on_submit:   Called with the current text when Enter is pressed.
            password:    If True, renders text as bullet characters (•).
        """
        super().__init__(rect)

        self._text:        str                          = text
        self._placeholder: str                          = placeholder
        self._max_length:  int | None                   = max_length
        self._on_change:   Callable[[str], None] | None = on_change
        self._on_submit:   Callable[[str], None] | None = on_submit
        self._password:    bool                         = password

        self.focusable:    bool  = True
        self._cursor_pos:  int   = len(text)   # index in text
        self._cursor_vis:  bool  = True         # blink state
        self._cursor_t:    float = 0.0          # blink accumulator

        self._font:    pygame.font.Font | None = None
        self._padding: int = 8

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        """Current text content."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set text programmatically and clamp cursor."""
        self._text = value
        self._cursor_pos = min(self._cursor_pos, len(value))

    def clear(self) -> None:
        """Clear the field and reset cursor to start."""
        self._text = ""
        self._cursor_pos = 0
        self._fire_change()

    # ── Focus ─────────────────────────────────────────────────────────────────

    def _on_focus_gained(self) -> None:
        """Called by FocusManager when focus is given via Tab."""
        self.focus()

    def _on_focus_lost(self) -> None:
        """Called by FocusManager when focus moves to another widget."""
        self.unfocus()

    def focus(self) -> None:
        """Give focus to this field and start text input mode."""
        if not self.focused:
            self.focused      = True
            self._cursor_vis  = True
            self._cursor_t    = 0.0
            pygame.key.start_text_input()

    def unfocus(self) -> None:
        """Remove focus and stop text input mode."""
        if self.focused:
            self.focused = False
            pygame.key.stop_text_input()

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        # Click to focus
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.focus()
                self._cursor_pos = len(self._text)
                return True
            else:
                self.unfocus()
                return False

        if not self.focused:
            return False

        # Character input via pygame TEXTINPUT event
        if event.type == pygame.TEXTINPUT:
            self._insert(event.text)
            return True

        # Key presses for navigation and control
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)

        return False

    def _handle_key(self, event: pygame.event.Event) -> bool:
        key  = event.key
        mods = event.mod

        if key == pygame.K_BACKSPACE:
            self._backspace()
            return True

        if key == pygame.K_DELETE:
            self._delete_forward()
            return True

        if key == pygame.K_LEFT:
            self._cursor_pos = max(0, self._cursor_pos - 1)
            self._reset_blink()
            return True

        if key == pygame.K_RIGHT:
            self._cursor_pos = min(len(self._text), self._cursor_pos + 1)
            self._reset_blink()
            return True

        if key == pygame.K_HOME:
            self._cursor_pos = 0
            self._reset_blink()
            return True

        if key == pygame.K_END:
            self._cursor_pos = len(self._text)
            self._reset_blink()
            return True

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._fire_submit()
            return True

        if key == pygame.K_ESCAPE:
            self.unfocus()
            return True

        return False

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Update cursor blink and focused state."""
        if self.focused:
            self._cursor_t += dt
            if self._cursor_t >= self.CURSOR_BLINK_RATE:
                self._cursor_t -= self.CURSOR_BLINK_RATE
                self._cursor_vis = not self._cursor_vis

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the input field onto surface."""
        if not self.visible:
            return

        theme  = get_theme()
        font   = self._get_font(theme)
        pad    = self._padding

        # Background
        bg      = theme.colours.bg_raised
        border  = (theme.colours.border_focus
                   if self.focused
                   else theme.colours.border)
        bw      = 2 if self.focused else 1
        radius  = theme.panel.surface.radius

        pygame.draw.rect(surface, bg, self.rect, border_radius=radius)
        pygame.draw.rect(surface, border, self.rect,
                         width=bw, border_radius=radius)

        display_text = self._display_text()
        if display_text:
            colour = (theme.colours.text
                      if self._text
                      else theme.colours.text_secondary)
            text_surf = font.render(display_text, True, colour)

            # Clip text to field interior
            clip_rect = pygame.Rect(
                self.rect.x + pad, self.rect.y,
                self.rect.width - pad * 2, self.rect.height
            )
            old_clip = surface.get_clip()
            surface.set_clip(clip_rect)

            text_y = self.rect.centery - text_surf.get_height() // 2
            text_x = self.rect.x + pad
            surface.blit(text_surf, (text_x, text_y))

            surface.set_clip(old_clip)

        # Cursor
        if self.focused and self._cursor_vis:
            self._draw_cursor(surface, font)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _insert(self, chars: str) -> None:
        """Insert characters at the cursor position."""
        for ch in chars:
            if self._max_length and len(self._text) >= self._max_length:
                break
            self._text = (self._text[:self._cursor_pos]
                          + ch
                          + self._text[self._cursor_pos:])
            self._cursor_pos += 1
        self._reset_blink()
        self._fire_change()

    def _backspace(self) -> None:
        """Delete the character before the cursor."""
        if self._cursor_pos > 0:
            self._text = (self._text[:self._cursor_pos - 1]
                          + self._text[self._cursor_pos:])
            self._cursor_pos -= 1
            self._reset_blink()
            self._fire_change()

    def _delete_forward(self) -> None:
        """Delete the character after the cursor."""
        if self._cursor_pos < len(self._text):
            self._text = (self._text[:self._cursor_pos]
                          + self._text[self._cursor_pos + 1:])
            self._reset_blink()
            self._fire_change()

    def _reset_blink(self) -> None:
        self._cursor_vis = True
        self._cursor_t   = 0.0

    def _display_text(self) -> str:
        """Return the text to render — masked if password, placeholder if empty."""
        if self._text:
            return "•" * len(self._text) if self._password else self._text
        if not self.focused:
            return self._placeholder
        return ""

    def _draw_cursor(
        self,
        surface: pygame.Surface,
        font:    pygame.font.Font,
    ) -> None:
        """Draw the text cursor at the current position."""
        before_cursor = self._text[:self._cursor_pos]
        if self._password:
            before_cursor = "•" * len(before_cursor)

        cursor_x = (self.rect.x + self._padding
                    + font.size(before_cursor)[0])
        cursor_y1 = self.rect.y + 6
        cursor_y2 = self.rect.bottom - 6

        theme = get_theme()
        pygame.draw.line(surface, theme.colours.text,
                         (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

    def _get_font(self, theme: object) -> pygame.font.Font:
        if self._font is None:
            from pygame_engine.theme.defaults import Theme
            t: Theme = theme  # type: ignore[assignment]
            self._font = pygame.font.SysFont(
                t.typography.family, t.typography.md
            )
        return self._font  # type: ignore[return-value]

    def _fire_change(self) -> None:
        if self._on_change is not None:
            self._on_change(self._text)

    def _fire_submit(self) -> None:
        if self._on_submit is not None:
            self._on_submit(self._text)