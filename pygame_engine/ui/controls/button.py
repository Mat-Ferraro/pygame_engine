"""
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

from pygame_engine.graphics.draw_utils import draw_surface_style
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
        self.focusable: bool = True

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
        """Return the current button label text."""
        return self._label.text

    @label.setter
    def label(self, value: str) -> None:
        """Return the current button label text."""
        self._label.text = value

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the button rect and reposition the internal label."""
        super().set_rect(rect)
        self._label.set_rect(pygame.Rect(rect))

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        # Keyboard activation when focused
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self._fire_click()
                return True

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
        """Update hover and pressed state from the current mouse position."""
        theme = get_theme()
        self._label.colour = (
            theme.button.text_disabled.colour
            if not self.enabled
            else theme.button.text.colour
        )

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the button onto surface."""
        if not self.visible:
            return

        theme = get_theme()
        style = self._resolve_style(theme)

        draw_surface_style(surface, self.rect, style)
        # Focus ring
        if self.focused and self.enabled:
            pygame.draw.rect(surface, theme.colours.border_focus,
                             self.rect.inflate(4, 4), width=2,
                             border_radius=style.radius + 2)
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