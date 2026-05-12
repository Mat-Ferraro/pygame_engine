"""
ui/controls/button.py

Button widget for pygame_engine.

A clickable rect with a text label. Supports normal, hovered, pressed,
and disabled visual states. Fires an ``on_click`` callback on mouse
release within bounds.

Theme integration is a future step. Button currently uses explicit
colour arguments with sensible defaults. When theme/runtime.py exists,
Button will fall back to theme values for colours and border radius.

Usage::

    from pygame_engine.ui.controls.button import Button

    btn = Button(
        rect=pygame.Rect(100, 200, 160, 48),
        label="Start Game",
        on_click=lambda: scene_manager.replace(GameScene()),
    )

    # Or assign the callback after construction:
    btn.on_click = my_handler
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.text.label import Label


class Button(Widget):
    """
    Clickable button with a text label.

    Visual states:
    - **normal**   — default idle appearance
    - **hovered**  — cursor is over the button
    - **pressed**  — left mouse button held down over the button
    - **disabled** — not enabled; does not respond to input

    ``on_click`` is called when the mouse button is released inside the
    button rect after being pressed inside it (standard click semantics).
    It is called with no arguments. Assign None to disable the callback.
    """

    # Default colour palette — will be replaced by theme lookups later.
    COLOUR_NORMAL:   tuple[int, int, int] = (60,  90,  160)
    COLOUR_HOVERED:  tuple[int, int, int] = (80,  115, 200)
    COLOUR_PRESSED:  tuple[int, int, int] = (40,  65,  120)
    COLOUR_DISABLED: tuple[int, int, int] = (60,  60,  70)

    COLOUR_BORDER:         tuple[int, int, int] = (120, 150, 220)
    COLOUR_BORDER_DISABLED: tuple[int, int, int] = (80,  80,  90)

    COLOUR_TEXT:          tuple[int, int, int] = (230, 230, 235)
    COLOUR_TEXT_DISABLED: tuple[int, int, int] = (120, 120, 130)

    BORDER_RADIUS: int = 6
    BORDER_WIDTH:  int = 1

    def __init__(
        self,
        rect: pygame.Rect,
        label: str = "",
        on_click: Callable[[], None] | None = None,
        font_size: int = 20,
    ) -> None:
        """
        Args:
            rect:     Position and size of this button.
            label:    Text displayed on the button face.
            on_click: Callable fired when the button is clicked.
                      Called with no arguments. May be None.
            font_size: Font size for the label text.
        """
        super().__init__(rect)

        self.on_click: Callable[[], None] | None = on_click

        self._pressed_inside: bool = False   # True while LMB held from inside

        # Internal label widget — shares this button's rect.
        self._label = Label(
            rect=pygame.Rect(rect),   # copy, not reference
            text=label,
            font_size=font_size,
            colour=self.COLOUR_TEXT,
            align="center",
        )

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def label(self) -> str:
        return self._label.text

    @label.setter
    def label(self, value: str) -> None:
        self._label.text = value

    def set_rect(self, rect: pygame.Rect) -> None:
        """Propagate rect changes to the internal label."""
        super().set_rect(rect)
        self._label.set_rect(pygame.Rect(rect))

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse press and release for click detection.

        Click semantics: press must start inside the button and release
        must also be inside the button to fire on_click.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed_inside = True
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed_inside:
                self._pressed_inside = False
                if self.rect.collidepoint(event.pos):
                    self._fire_click()
                return True

        return False

    def _fire_click(self) -> None:
        if self.on_click is not None:
            self.on_click()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        # Sync label text colour with current enabled state.
        self._label.colour = (
            self.COLOUR_TEXT_DISABLED if not self.enabled
            else self.COLOUR_TEXT
        )

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        bg, border = self._resolve_colours()

        pygame.draw.rect(surface, bg, self.rect,
                         border_radius=self.BORDER_RADIUS)
        pygame.draw.rect(surface, border, self.rect,
                         width=self.BORDER_WIDTH,
                         border_radius=self.BORDER_RADIUS)

        self._label.render(surface)

    def _resolve_colours(
        self,
    ) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        """Return (background, border) colours for the current state."""
        if not self.enabled:
            return self.COLOUR_DISABLED, self.COLOUR_BORDER_DISABLED
        if self._pressed_inside and self.hovered:
            return self.COLOUR_PRESSED, self.COLOUR_BORDER
        if self.hovered:
            return self.COLOUR_HOVERED, self.COLOUR_BORDER
        return self.COLOUR_NORMAL, self.COLOUR_BORDER
