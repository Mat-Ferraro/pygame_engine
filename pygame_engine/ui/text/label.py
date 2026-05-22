"""
from pygame_engine.ui.text.label import Label

    # Theme-styled (uses theme.label.text defaults)
    label = Label(rect, "Hello")

    # Explicit override
    label = Label(rect, "Hello", font_size=28, colour=(255, 200, 0))
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget

_UNSET = object()   # sentinel for "caller did not supply this argument"


class Label(Widget):
    """
    Single-line text display widget.

    Style values fall back to the active theme when not explicitly
    supplied. The font is created once at construction and cached.
    The rendered text surface is cached and re-rendered only when text,
    colour, or rect changes (dirty-flag pattern).

    Does not handle events. Does not manage children.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        text: str = "",
        font_size: object = _UNSET,
        colour:    object = _UNSET,
        align:     str    = "center",
        font_name: object = _UNSET,
        bold:      bool   = False,
    ) -> None:
        """
        Args:
            rect:      Position and size of this label.
            text:      Text to display.
            font_size: Font size in points. Defaults to ``theme.label.text.font_size``.
            colour:    RGB text colour. Defaults to ``theme.label.text.colour``.
            align:     Horizontal alignment — ``"left"``, ``"center"``, ``"right"``.
            font_name: Comma-separated SysFont hints. Defaults to ``theme.typography.family``.
            bold:      Render bold text.
        """
        super().__init__(rect)

        theme = get_theme()

        self._text:      str                  = text
        self._colour:    tuple[int, int, int] = (
            colour if colour is not _UNSET                        # type: ignore[assignment]
            else theme.label.text.colour
        )
        self._font_size: int = (
            font_size if font_size is not _UNSET                  # type: ignore[assignment]
            else theme.label.text.font_size
        )
        self._font_name: str = (
            font_name if font_name is not _UNSET                  # type: ignore[assignment]
            else theme.typography.family
        )
        self._align: str  = align
        self._bold:  bool = bold

        self._font:    pygame.font.Font | None = None
        self._surface: pygame.Surface | None   = None
        self._dirty:   bool                    = True

        self._build_font()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def text(self) -> str:
        """Return the current label text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Return the current label text."""
        if value != self._text:
            self._text = value
            self._dirty = True

    @property
    def colour(self) -> tuple[int, int, int]:
        """Return the current text colour."""
        return self._colour

    @colour.setter
    def colour(self, value: tuple[int, int, int]) -> None:
        """Return the current text colour."""
        if value != self._colour:
            self._colour = value
            self._dirty = True

    @property
    def align(self) -> str:
        """Return the current text alignment."""
        return self._align

    @align.setter
    def align(self, value: str) -> None:
        """Return the current text alignment."""
        if value != self._align:
            self._align = value
            self._dirty = True

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the label rect and reflow text alignment."""
        self.rect = rect
        self._dirty = True

    # ── Frame methods ─────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the label onto surface."""
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
        if self._font is None:
            return
        self._surface = self._font.render(self._text, True, self._colour)
        self._dirty = False

    def _align_rect(self, text_rect: pygame.Rect) -> pygame.Rect:
        text_rect.centery = self.rect.centery
        if self._align == "left":
            text_rect.left = self.rect.left
        elif self._align == "right":
            text_rect.right = self.rect.right
        else:
            text_rect.centerx = self.rect.centerx
        return text_rect