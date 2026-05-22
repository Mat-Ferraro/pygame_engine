"""
Usage::

    from pygame_engine.ui.controls.checkbox import Checkbox

    fullscreen = Checkbox(
        rect=pygame.Rect(100, 200, 200, 32),
        label="Fullscreen",
        checked=False,
        on_change=lambda v: apply_fullscreen(v),
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


from typing import Callable

import pygame

from pygame_engine.ui.base.widget import Widget


class Checkbox(Widget):
    """
    Boolean on/off toggle with an inline text label.

    The clickable area covers the entire rect. The box is drawn on the
    left; the label follows to the right. Keyboard: Space or Enter toggles
    when focused.

    Args:
        rect:      Position and size. Height should be at least 24px.
        label:     Text shown to the right of the box.
        checked:   Initial state.
        on_change: Called with the new bool whenever the state changes.
    """

    BOX_SIZE = 20   # square checkbox size in pixels

    def __init__(
        self,
        rect:      pygame.Rect,
        label:     str  = "",
        checked:   bool = False,
        on_change: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(rect)
        self._checked  = checked
        self.label     = label
        self.on_change = on_change
        self.focusable = True
        self._font: pygame.font.Font | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def checked(self) -> bool:
        """Return the current checked state."""
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        """Return the current checked state."""
        if value != self._checked:
            self._checked = value
            if self.on_change:
                self.on_change(self._checked)

    def toggle(self) -> None:
        """Flip the checked state."""
        self.checked = not self._checked

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.toggle()
                return True

        if event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.toggle()
                return True

        return False

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the checkbox onto surface."""
        if not self.visible:
            return

        theme = ctx.theme
        colours = theme.colours

        # Box rect (left-aligned, vertically centred)
        box_x = self.rect.x
        box_y = self.rect.centery - self.BOX_SIZE // 2
        box   = pygame.Rect(box_x, box_y, self.BOX_SIZE, self.BOX_SIZE)

        # Box background
        bg = theme.button.normal.bg if self._checked else colours.bg_raised
        pygame.draw.rect(surface, bg, box, border_radius=4)

        # Box border
        border_col = theme.button.hovered.border if self.focused else colours.border
        pygame.draw.rect(surface, border_col, box, width=1, border_radius=4)

        # Checkmark
        if self._checked:
            pad = 4
            pts = [
                (box.x + pad,             box.centery),
                (box.x + self.BOX_SIZE // 2 - 1, box.bottom - pad - 1),
                (box.right - pad,         box.y + pad + 1),
            ]
            pygame.draw.lines(surface, colours.bg_dark, False, pts, width=2)

        # Focus ring
        if self.focused and self.enabled:
            pygame.draw.rect(surface, colours.border_focus,
                             box.inflate(4, 4), width=2, border_radius=6)

        # Label
        if self.label:
            if self._font is None:
                self._font = pygame.font.SysFont(
                    theme.typography.family, theme.typography.md
                )
            col  = (colours.text if self.enabled
                    else theme.button.text_disabled.colour)
            text = self._font.render(self.label, True, col)
            tx   = box.right + 10
            ty   = self.rect.centery - text.get_height() // 2
            surface.blit(text, (tx, ty))