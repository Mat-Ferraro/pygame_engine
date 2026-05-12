"""
ui/text/label.py

Label widget for pygame_engine.

Renders a single line of text within its rect. Supports horizontal
alignment, colour, and font size. Font is created once at construction
and cached — not recreated every frame.

Theme integration is a future step. For now, Label accepts explicit
style arguments with sensible defaults. When theme/runtime.py exists,
Label will fall back to theme values when arguments are not supplied.

Usage::

    from pygame_engine.ui.text.label import Label

    label = Label(
        rect=pygame.Rect(100, 100, 200, 40),
        text="Hello, world",
        font_size=22,
        colour=(220, 220, 220),
        align="center",
    )
"""

from __future__ import annotations

import pygame

from pygame_engine.ui.base.widget import Widget


class Label(Widget):
    """
    Single-line text display widget.

    Does not handle events (returns False from handle_event).
    Does not manage children.

    Alignment controls how the text sits horizontally within the rect.
    Vertical centering is always applied.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        text: str = "",
        font_size: int = 20,
        colour: tuple[int, int, int] = (220, 220, 220),
        align: str = "center",
        font_name: str = "segoeui,helvetica,arial",
        bold: bool = False,
    ) -> None:
        """
        Args:
            rect:      Position and size of this label.
            text:      Text to display.
            font_size: Font size in points.
            colour:    Text colour as an RGB tuple.
            align:     Horizontal alignment — ``"left"``, ``"center"``,
                       or ``"right"``.
            font_name: Comma-separated font name hints for SysFont.
            bold:      Whether to render the font bold.
        """
        super().__init__(rect)

        self._text:      str                    = text
        self._colour:    tuple[int, int, int]   = colour
        self._align:     str                    = align
        self._font_size: int                    = font_size
        self._font_name: str                    = font_name
        self._bold:      bool                   = bold

        self._font:    pygame.font.Font | None  = None
        self._surface: pygame.Surface | None    = None   # cached render
        self._dirty:   bool                     = True   # needs re-render

        self._build_font()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self._dirty = True

    @property
    def colour(self) -> tuple[int, int, int]:
        return self._colour

    @colour.setter
    def colour(self, value: tuple[int, int, int]) -> None:
        if value != self._colour:
            self._colour = value
            self._dirty = True

    @property
    def align(self) -> str:
        return self._align

    @align.setter
    def align(self, value: str) -> None:
        if value != self._align:
            self._align = value
            self._dirty = True

    def set_rect(self, rect: pygame.Rect) -> None:
        """Override to invalidate cached render on resize."""
        self.rect = rect
        self._dirty = True

    # ── Frame methods ─────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if self._dirty:
            self._render_text()
        if self._surface is not None:
            dest = self._align_rect(self._surface.get_rect())
            surface.blit(self._surface, dest)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_font(self) -> None:
        self._font = pygame.font.SysFont(
            self._font_name, self._font_size, bold=self._bold
        )
        self._dirty = True

    def _render_text(self) -> None:
        """Re-render the text surface and cache it."""
        if self._font is None:
            return
        self._surface = self._font.render(self._text, True, self._colour)
        self._dirty = False

    def _align_rect(self, text_rect: pygame.Rect) -> pygame.Rect:
        """Position the text surface rect within self.rect."""
        # Always centre vertically
        text_rect.centery = self.rect.centery

        if self._align == "left":
            text_rect.left = self.rect.left
        elif self._align == "right":
            text_rect.right = self.rect.right
        else:  # center
            text_rect.centerx = self.rect.centerx

        return text_rect
