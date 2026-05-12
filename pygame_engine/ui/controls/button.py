"""
ui/controls/button.py

Button widget for pygame_engine.

Reads all visual style values from the active theme. Per-instance
colour overrides are not yet supported — override the theme instead.

Usage::

    from pygame_engine.ui.controls.button import Button

    btn = Button(
        rect=pygame.Rect(100, 200, 160, 48),
        label="Start Game",
        on_click=lambda: scene_manager.replace(GameScene()),
    )
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.text.label import Label


class Button(Widget):
    """
    Clickable button with a text label.

    Visual states — normal, hovered, pressed, disabled — are all styled
    through the active theme (``theme.button.*``).

    Click semantics: ``on_click`` fires only when the mouse is pressed
    inside the button AND released inside it. Releasing outside after
    pressing inside cancels the click without consuming the release event.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        label: str = "",
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """
        Args:
            rect:     Position and size of this button.
            label:    Text displayed on the button face.
            on_click: Callable fired on click. Called with no arguments.
        """
        super().__init__(rect)

        self.on_click: Callable[[], None] | None = on_click
        self._pressed_inside: bool = False

        theme = get_theme()
        self._label = Label(
            rect=pygame.Rect(rect),
            text=label,
            font_size=theme.button.text.font_size,
            colour=theme.button.text.colour,
            font_name=theme.typography.family,
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
        super().set_rect(rect)
        self._label.set_rect(pygame.Rect(rect))

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed_inside = True
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed_inside:
                self._pressed_inside = False
                if self.rect.collidepoint(event.pos):
                    self._fire_click()
                    return True   # consumed — click completed inside
            return False          # not our press, or released outside

        return False

    def _fire_click(self) -> None:
        if self.on_click is not None:
            self.on_click()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        theme = get_theme()
        self._label.colour = (
            theme.button.text_disabled.colour
            if not self.enabled
            else theme.button.text.colour
        )

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        theme = get_theme()
        style = self._resolve_style(theme)

        pygame.draw.rect(surface, style.bg, self.rect,
                         border_radius=style.radius)
        if style.border_width > 0:
            pygame.draw.rect(surface, style.border, self.rect,
                             width=style.border_width,
                             border_radius=style.radius)

        self._label.render(surface)

    def _resolve_style(self, theme: object) -> object:  # type: ignore[return]
        """Return the SurfaceStyle for the current interaction state."""
        from pygame_engine.theme.defaults import Theme  # local to avoid circular
        t: Theme = theme  # type: ignore[assignment]
        if not self.enabled:
            return t.button.disabled
        if self._pressed_inside and self.hovered:
            return t.button.pressed
        if self.hovered:
            return t.button.hovered
        return t.button.normal
