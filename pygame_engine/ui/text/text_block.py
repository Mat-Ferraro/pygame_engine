from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


import pygame

from pygame_engine.graphics.text_utils import wrap_text
from pygame_engine.ui.base.widget import Widget

_UNSET = object()


class TextBlock(Widget):
    """
    Wrapped multi-line text widget.

    Text is wrapped to the available width inside the widget rect.
    Rendering is cached and invalidated when text, style, rect, padding,
    or line spacing changes.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        text: str = "",
        *,
        font_size: int | object = _UNSET,
        colour: tuple[int, int, int] | object = _UNSET,
        font_name: str | object = _UNSET,
        align: str = "left",
        padding: int = 0,
        line_spacing: int = 4,
    ) -> None:
        super().__init__(rect)

        self._text         = text
        self._font_size    = font_size
        self._colour       = colour
        self._font_name    = font_name
        self._align        = align
        self._padding      = padding
        self._line_spacing = line_spacing

        self._cache_surface: pygame.Surface | None = None
        self._dirty: bool = True

    @property
    def text(self) -> str:
        """Return the current text content."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Return the current text content."""
        if value != self._text:
            self._text  = value
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

    @property
    def padding(self) -> int:
        """Return the current padding in pixels."""
        return self._padding

    @padding.setter
    def padding(self, value: int) -> None:
        """Return the current padding in pixels."""
        if value != self._padding:
            self._padding = value
            self._dirty   = True

    @property
    def line_spacing(self) -> int:
        """Return the additional line spacing in pixels."""
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, value: int) -> None:
        """Return the additional line spacing in pixels."""
        if value != self._line_spacing:
            self._line_spacing = value
            self._dirty        = True

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the text block rect and mark the cache as dirty."""
        super().set_rect(rect)
        self._dirty = True

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the text block onto surface, rebuilding the cache if dirty."""
        if not self.visible:
            return
        if self._dirty or self._cache_surface is None:
            self._cache_surface = self._build_surface(ctx)
            self._dirty         = False
        if self._cache_surface is not None:
            surface.blit(self._cache_surface, self.rect.topleft)

    def _build_surface(self, ctx: "RenderContext") -> pygame.Surface:
        theme = ctx.theme

        font_size = (
            theme.label.text.font_size
            if self._font_size is _UNSET else self._font_size
        )
        colour = (
            theme.label.text.colour
            if self._colour is _UNSET else self._colour
        )
        font_name = (
            theme.typography.family
            if self._font_name is _UNSET else self._font_name
        )

        width  = max(1, self.rect.width)
        height = max(1, self.rect.height)

        out  = pygame.Surface((width, height), pygame.SRCALPHA)
        font = pygame.font.SysFont(font_name, font_size)

        inner_width = max(1, width - self._padding * 2)
        # Delegates to the shared utility in pygame_engine.graphics.text_utils
        lines = wrap_text(font, self._text, inner_width)

        y = self._padding
        for line in lines:
            rendered = font.render(line if line else " ", True, colour)

            line_rect = rendered.get_rect()
            if self._align == "center":
                line_rect.centerx = width // 2
            elif self._align == "right":
                line_rect.right = width - self._padding
            else:
                line_rect.x = self._padding

            line_rect.y = y
            if line_rect.bottom > height:
                break

            out.blit(rendered, line_rect)
            y += rendered.get_height() + self._line_spacing

        return out