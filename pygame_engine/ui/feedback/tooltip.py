"""
A small floating label that appears near the mouse cursor to provide
context for a hovered widget. The tooltip is shown and hidden externally
— the owning scene or widget calls show()/hide() based on hover state.

The tooltip positions itself relative to the mouse position each frame,
with a configurable offset and automatic clamping to screen bounds.

Usage::

    from pygame_engine.ui.feedback.tooltip import Tooltip

    # Create once, typically in scene.on_enter
    tooltip = Tooltip(screen_rect, "Click to confirm")

    # In a widget's update or the scene's update:
    if button.hovered:
        tooltip.show(input_manager.get_mouse_pos())
    else:
        tooltip.hide()

    # In scene.update:
    tooltip.update(dt)

    # In scene.render, after all other widgets:
    tooltip.render(surface)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.graphics.surfaces import blit_alpha_surface, make_alpha_surface
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class Tooltip(Widget):
    """
    Small floating label shown near the mouse cursor.

    Positioning
    -----------
    The tooltip follows the mouse. Call ``show(mouse_pos)`` each frame
    the tooltip should be visible — it updates its position automatically.
    The tooltip is clamped inside ``screen_bounds`` so it never draws
    off-screen.

    Rendering
    ---------
    Render the tooltip last (after all other widgets) so it always
    appears on top. The tooltip renders nothing when not visible.

    Fade
    ----
    The tooltip fades in over ``fade_in_duration`` seconds when shown.
    It appears instantly (no fade) when ``fade_in_duration`` is 0.
    """

    # Default offset from the mouse cursor in pixels
    DEFAULT_OFFSET: tuple[int, int] = (14, 18)

    def __init__(
        self,
        screen_bounds: pygame.Rect,
        text: str = "",
        offset: tuple[int, int] = DEFAULT_OFFSET,
        fade_in_duration: float = 0.12,
        padding: int = 8,
    ) -> None:
        """
        Args:
            screen_bounds:    The area the tooltip must stay within.
            text:             Tooltip text.
            offset:           (dx, dy) offset from the mouse cursor.
            fade_in_duration: Fade-in time in seconds. 0 = instant.
            padding:          Inner padding between text and background edge.
        """
        # Start with a zero rect — positioned dynamically in show()
        super().__init__(pygame.Rect(0, 0, 0, 0))
        self.visible = False

        self._screen_bounds:    pygame.Rect       = screen_bounds
        self._text:             str               = text
        self._offset:           tuple[int, int]   = offset
        self._fade_in_duration: float             = fade_in_duration
        self._padding:          int               = padding

        self._alpha:      float                    = 0.0
        self._font:       pygame.font.Font | None  = None
        self._text_surf:  pygame.Surface | None    = None
        self._bg_surf:    pygame.Surface | None    = None
        self._dirty:      bool                     = True

        self._build_font()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        """Return the current tooltip text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Return the current tooltip text."""
        if value != self._text:
            self._text = value
            self._dirty = True

    def show(self, mouse_pos: tuple[int, int]) -> None:
        """
        Make the tooltip visible and position it near ``mouse_pos``.

        Call this every frame the tooltip should be displayed (typically
        while the target widget is hovered). The tooltip will update its
        position each call.

        Args:
            mouse_pos: Current mouse cursor position in screen coordinates.
        """
        self.visible = True
        self._position_near(mouse_pos)

    def hide(self) -> None:
        """Hide the tooltip and reset its fade state."""
        self.visible = False
        self._alpha  = 0.0

    # ── Frame methods ─────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Update tooltip visibility based on hover state."""
        if not self.visible:
            return
        if self._fade_in_duration > 0:
            self._alpha = min(1.0, self._alpha + dt / self._fade_in_duration)
        else:
            self._alpha = 1.0

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the tooltip onto surface if visible."""
        if not self.visible or self._alpha <= 0:
            return
        if self._dirty:
            self._rebuild_surfaces()
        if self._bg_surf is None or self._text_surf is None:
            return

        blit_alpha_surface(surface, self._bg_surf, self.rect.topleft, self._alpha)
        blit_alpha_surface(surface, self._text_surf, (
            self.rect.x + self._padding,
            self.rect.y + self._padding,
        ), self._alpha)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_font(self) -> None:
        theme = get_theme()
        self._font = pygame.font.SysFont(
            theme.typography.family,
            theme.typography.xs,
        )
        self._dirty = True

    def _rebuild_surfaces(self) -> None:
        """Rebuild the text and background surfaces from current theme."""
        if self._font is None:
            return

        theme = get_theme()
        self._text_surf = self._font.render(
            self._text, True, theme.colours.text
        )

        tw = self._text_surf.get_width()  + self._padding * 2
        th = self._text_surf.get_height() + self._padding * 2

        self._bg_surf = make_alpha_surface(tw, th)
        pygame.draw.rect(
            self._bg_surf,
            (*theme.colours.bg_raised, 230),
            pygame.Rect(0, 0, tw, th),
            border_radius=4,
        )
        pygame.draw.rect(
            self._bg_surf,
            (*theme.colours.border, 180),
            pygame.Rect(0, 0, tw, th),
            width=1,
            border_radius=4,
        )
        self._dirty = False

    def _position_near(self, mouse_pos: tuple[int, int]) -> None:
        """Position the tooltip near the mouse, clamped to screen bounds."""
        if self._dirty:
            self._rebuild_surfaces()
        if self._bg_surf is None:
            return

        w = self._bg_surf.get_width()
        h = self._bg_surf.get_height()
        dx, dy = self._offset

        x = mouse_pos[0] + dx
        y = mouse_pos[1] + dy

        # Clamp so the tooltip stays fully inside screen bounds
        x = max(self._screen_bounds.left,
                min(x, self._screen_bounds.right  - w))
        y = max(self._screen_bounds.top,
                min(y, self._screen_bounds.bottom - h))

        self.rect = pygame.Rect(x, y, w, h)