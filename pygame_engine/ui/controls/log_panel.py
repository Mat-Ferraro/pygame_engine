"""
LogPanel — scrollable text log with append() and auto-scroll.

A read-only panel that accumulates lines of text and displays them
newest-at-bottom. Auto-scrolls to follow new entries by default.
Used for event logs, combat narration, training results, status feeds.

Usage::

    from pygame_engine.ui.controls.log_panel import LogPanel

    log = LogPanel(
        rect=pygame.Rect(40, 500, 600, 300),
        max_lines=200,
    )

    log.append("Hero Kira levelled up!")
    log.append("Campaign round resolved.", colour=(180, 230, 180))
    log.clear()
"""

from __future__ import annotations

import pygame

from pygame_engine.graphics.draw_utils import draw_rect_bordered
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class LogPanel(Widget):
    """
    Scrollable read-only text log.

    Lines are stored as ``(text, colour)`` tuples. When ``max_lines`` is
    reached the oldest lines are dropped automatically.

    Auto-scroll follows new entries unless the user has scrolled up manually.
    Scrolling back to the bottom re-enables auto-scroll.

    Args:
        rect:       Widget rect.
        max_lines:  Maximum stored lines. Oldest are dropped when exceeded.
        line_spacing: Extra pixels between lines.
        padding:    Inner padding from edge to text.
        font_size:  Override font size. None = theme ``sm``.
    """

    SCROLLBAR_W   = 8
    TRACK_COLOUR  = (40,  44,  60)
    THUMB_COLOUR  = (90,  100, 130)
    THUMB_HOVERED = (120, 135, 170)

    def __init__(
        self,
        rect:          pygame.Rect,
        max_lines:     int = 500,
        line_spacing:  int = 4,
        padding:       int = 10,
        font_size:     int | None = None,
    ) -> None:
        super().__init__(rect)
        self.max_lines    = max_lines
        self.line_spacing = line_spacing
        self.padding      = padding
        self._font_size   = font_size

        self._lines:    list[tuple[str, tuple]] = []   # (text, colour)
        self._scroll_y: float = 0.0
        self._auto_scroll: bool = True
        self._font:     pygame.font.Font | None = None
        self._line_h:   int = 0
        self._dirty_font: bool = True

    # ── Public API ────────────────────────────────────────────────────────────

    def append(
        self,
        text: str,
        colour: tuple[int, int, int] | None = None,
    ) -> None:
        """Add a line to the log. Drops oldest if max_lines exceeded."""
        theme = get_theme()
        col   = colour or theme.colours.text_secondary
        self._lines.append((text, col))
        if len(self._lines) > self.max_lines:
            self._lines = self._lines[-self.max_lines:]
        if self._auto_scroll:
            self._scroll_y = self._max_scroll()

    def append_lines(
        self,
        lines: list[str],
        colour: tuple[int, int, int] | None = None,
        auto_scroll: bool = True,
    ) -> None:
        """Append multiple lines at once."""
        for line in lines:
            self.append(line, colour)
        if auto_scroll:
            self._scroll_y = self._max_scroll()

    def clear(self) -> None:
        """Remove all lines."""
        self._lines    = []
        self._scroll_y = 0.0

    def scroll_to_bottom(self) -> None:
        self._scroll_y    = self._max_scroll()
        self._auto_scroll = True

    @property
    def line_count(self) -> int:
        return len(self._lines)

    # ── Events ────────────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                old = self._scroll_y
                self._scroll_y = max(0.0, min(
                    self._scroll_y - event.y * self._line_height() * 2,
                    self._max_scroll(),
                ))
                if self._scroll_y < old:
                    self._auto_scroll = False
                elif self._scroll_y >= self._max_scroll():
                    self._auto_scroll = True
                return True
        return False

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        theme = get_theme()
        self._ensure_font(theme)

        draw_rect_bordered(
            surface, self.rect,
            fill=theme.colours.bg_base,
            border=theme.colours.border,
            radius=theme.panel.surface.radius,
        )

        lh   = self._line_height()
        clip = pygame.Rect(
            self.rect.x + 2,
            self.rect.y + 2,
            self.rect.width - self.SCROLLBAR_W - 4,
            self.rect.height - 4,
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip)

        if self._lines:
            for i, (text, col) in enumerate(self._lines):
                y = (self.rect.y + self.padding
                     + i * lh
                     - int(self._scroll_y))
                if y + lh < clip.top or y > clip.bottom:
                    continue
                surf = self._font.render(text, True, col)  # type: ignore[union-attr]
                surface.blit(surf, (self.rect.x + self.padding, y))
        else:
            placeholder = self._font.render(  # type: ignore[union-attr]
                "Log is empty.", True, theme.colours.text_secondary)
            surface.blit(placeholder,
                         (self.rect.x + self.padding, self.rect.y + self.padding))

        surface.set_clip(old_clip)

        if self._max_scroll() > 0:
            self._draw_scrollbar(surface)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _ensure_font(self, theme) -> None:
        if self._dirty_font or self._font is None:
            size = self._font_size or theme.typography.sm
            self._font = pygame.font.SysFont(theme.typography.family, size)
            self._dirty_font = False

    def _line_height(self) -> int:
        if self._font is None:
            return 18
        return self._font.get_linesize() + self.line_spacing

    def _total_height(self) -> float:
        return len(self._lines) * self._line_height()

    def _max_scroll(self) -> float:
        visible = self.rect.height - self.padding * 2
        return max(0.0, self._total_height() - visible)

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        bx = self.rect.right - self.SCROLLBAR_W
        bh = self.rect.height
        track = pygame.Rect(bx, self.rect.y, self.SCROLLBAR_W, bh)
        pygame.draw.rect(surface, self.TRACK_COLOUR, track, border_radius=4)
        total  = max(self._total_height(), 1)
        ratio  = min(1.0, bh / total)
        th     = max(20, int(bh * ratio))
        ms     = self._max_scroll()
        pct    = self._scroll_y / ms if ms > 0 else 1.0
        ty     = self.rect.y + int((bh - th) * pct)
        colour = self.THUMB_HOVERED if self.hovered else self.THUMB_COLOUR
        pygame.draw.rect(surface, colour,
                         pygame.Rect(bx + 1, ty, self.SCROLLBAR_W - 2, th),
                         border_radius=4)
