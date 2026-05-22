"""
Usage::

    from pygame_engine.ui.controls.list_view import ListView

    heroes = ListView(
        rect=pygame.Rect(40, 150, 760, 500),
        row_height=72,
        row_gap=6,
        on_select=lambda hero: self.set_selected(hero),
    )
    heroes.set_items(state.roster)
    heroes.row_renderer = self.draw_hero_row   # (surface, item, rect, selected, hovered)

    # frame loop:
    heroes.handle_event(event)
    heroes.update(dt)
    heroes.render(surface)

    # read selection:
    hero = heroes.selected_item
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.app.render_context import RenderContext


from typing import Callable

import pygame

from pygame_engine.graphics.draw_utils import draw_rect_bordered
from pygame_engine.ui.base.widget import Widget


class ListView(Widget):
    """
    Scrollable list of items with hover, selection, and custom row rendering.

    Row renderer signature::

        def my_renderer(
            surface:  pygame.Surface,
            item:     Any,
            rect:     pygame.Rect,
            selected: bool,
            hovered:  bool,
        ) -> None: ...

    If no ``row_renderer`` is set, rows fall back to a plain styled rect
    with ``str(item)`` as the label.

    Keyboard navigation (when focused): Up/Down to move selection.

    Args:
        rect:          Viewport rect in screen coordinates.
        row_height:    Height of each row in pixels.
        row_gap:       Vertical gap between rows in pixels.
        padding:       Inner padding from viewport edge to rows.
        on_select:     Called with the newly selected item (or None on clear).
        row_renderer:  Callable for custom row appearance.
        scroll_speed:  Pixels scrolled per mouse-wheel tick.
    """

    SCROLLBAR_W   = 8
    TRACK_COLOUR  = (40,  44,  60)
    THUMB_COLOUR  = (90,  100, 130)
    THUMB_HOVERED = (120, 135, 170)

    def __init__(
        self,
        rect:          pygame.Rect,
        row_height:    int            = 56,
        row_gap:       int            = 4,
        padding:       int            = 8,
        on_select:     Callable | None = None,
        row_renderer:  Callable | None = None,
        scroll_speed:  int            = 30,
    ) -> None:
        super().__init__(rect)
        self.row_height   = row_height
        self.row_gap      = row_gap
        self.padding      = padding
        self.on_select    = on_select
        self.row_renderer = row_renderer
        self.scroll_speed = scroll_speed
        self.focusable    = True

        self._items:       list       = []
        self._selected_id: int | None = None   # id() of selected item
        self._hovered_i:   int        = -1
        self._scroll_y:    float      = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def set_items(self, items: list) -> None:
        """Replace the item list. Preserves selection if the same object
        still exists in the new list; clears it otherwise."""
        self._items = list(items)
        if self._selected_id is not None:
            if not any(id(i) == self._selected_id for i in self._items):
                self._selected_id = None
        self._scroll_y = max(0.0, min(self._scroll_y, self._max_scroll()))

    def append_item(self, item) -> None:
        """Add a single item without clearing the existing list."""
        self._items.append(item)

    def clear(self) -> None:
        """Remove all items and clear selection."""
        self._items       = []
        self._selected_id = None
        self._scroll_y    = 0.0

    @property
    def selected_item(self):
        """The currently selected item, or None."""
        if self._selected_id is None:
            return None
        for item in self._items:
            if id(item) == self._selected_id:
                return item
        return None

    def select(self, item) -> None:
        """Programmatically select an item and scroll it into view.
        Fires ``on_select`` if the selection changes."""
        if item in self._items:
            new_id = id(item)
            changed = (new_id != self._selected_id)
            self._selected_id = new_id
            self._scroll_into_view(self._items.index(item))
            if changed and self.on_select:
                self.on_select(item)

    def deselect(self) -> None:
        """Clear the current selection."""
        self._selected_id = None

    def scroll_to_top(self) -> None:
        """Scroll to the first item in the list."""
        self._scroll_y = 0.0

    def scroll_to_bottom(self) -> None:
        """Scroll to the last item in the list."""
        self._scroll_y = self._max_scroll()

    # ── Events ────────────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self._scroll_y = max(0.0, min(
                    self._scroll_y - event.y * self.scroll_speed,
                    self._max_scroll(),
                ))
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                i = self._index_at(event.pos)
                if i >= 0:
                    self._do_select(i)
                    return True

        if event.type == pygame.KEYDOWN and self.focused and self._items:
            if event.key == pygame.K_UP:
                cur = self._current_index()
                self._do_select(max(0, cur - 1) if cur > 0 else 0)
                return True
            if event.key == pygame.K_DOWN:
                cur  = self._current_index()
                last = len(self._items) - 1
                self._do_select(min(last, cur + 1) if cur >= 0 else 0)
                return True

        return False

    def update(self, dt: float) -> None:
        """Update hover state and scroll position."""
        mouse = pygame.mouse.get_pos()
        self._hovered_i = (
            self._index_at(mouse) if self.rect.collidepoint(mouse) else -1
        )

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface, ctx: "RenderContext") -> None:
        """Draw the list view onto surface."""
        if not self.visible:
            return

        theme = ctx.theme

        draw_rect_bordered(
            surface, self.rect,
            fill=theme.colours.bg_base,
            border=theme.colours.border,
            radius=theme.panel.surface.radius,
        )

        clip = pygame.Rect(
            self.rect.x,
            self.rect.y,
            self.rect.width - self.SCROLLBAR_W,
            self.rect.height,
        )
        old_clip = surface.get_clip()
        surface.set_clip(clip)

        if not self._items:
            font = pygame.font.SysFont(theme.typography.family, theme.typography.sm)
            surf = font.render("No items.", True, theme.colours.text_secondary)
            surface.blit(surf, (self.rect.x + 16, self.rect.y + 16))
        else:
            for i, item in enumerate(self._items):
                rr = self._row_rect(i)
                if rr.bottom < clip.top or rr.top > clip.bottom:
                    continue
                is_sel = (id(item) == self._selected_id)
                is_hov = (i == self._hovered_i) and not is_sel
                if self.row_renderer:
                    self.row_renderer(surface, item, rr, is_sel, is_hov)
                else:
                    self._default_row(surface, item, rr, is_sel, is_hov, theme)

        surface.set_clip(old_clip)

        if self._max_scroll() > 0:
            self._draw_scrollbar(surface)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _row_rect(self, index: int) -> pygame.Rect:
        y = (self.rect.y + self.padding
             + index * (self.row_height + self.row_gap)
             - int(self._scroll_y))
        return pygame.Rect(
            self.rect.x + self.padding,
            y,
            self.rect.width - self.padding * 2 - self.SCROLLBAR_W,
            self.row_height,
        )

    def _index_at(self, pos: tuple) -> int:
        for i in range(len(self._items)):
            if self._row_rect(i).collidepoint(pos):
                return i
        return -1

    def _current_index(self) -> int:
        if self._selected_id is None:
            return -1
        for i, item in enumerate(self._items):
            if id(item) == self._selected_id:
                return i
        return -1

    def _do_select(self, index: int) -> None:
        item   = self._items[index]
        new_id = id(item)
        changed = (new_id != self._selected_id)
        self._selected_id = new_id
        self._scroll_into_view(index)
        if changed and self.on_select:
            self.on_select(item)

    def _scroll_into_view(self, index: int) -> None:
        rr = self._row_rect(index)
        if rr.top < self.rect.top:
            self._scroll_y = max(0.0,
                self._scroll_y - (self.rect.top - rr.top))
        elif rr.bottom > self.rect.bottom:
            self._scroll_y = min(self._max_scroll(),
                self._scroll_y + (rr.bottom - self.rect.bottom))

    def _max_scroll(self) -> float:
        total   = len(self._items) * (self.row_height + self.row_gap)
        visible = self.rect.height - self.padding * 2
        return max(0.0, float(total - visible))

    def _default_row(self, surface, item, rr, is_sel, is_hov, theme) -> None:
        if is_sel:
            bg, border = theme.button.pressed.bg, theme.colours.border
        elif is_hov:
            bg, border = theme.colours.bg_raised, theme.colours.border
        else:
            bg, border = theme.colours.bg_base, theme.colours.border
        draw_rect_bordered(surface, rr, fill=bg, border=border, radius=4)
        font = pygame.font.SysFont(theme.typography.family, theme.typography.sm)
        surf = font.render(str(item), True, theme.colours.text)
        surface.blit(surf, (rr.x + 8, rr.centery - surf.get_height() // 2))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        bx = self.rect.right - self.SCROLLBAR_W
        bh = self.rect.height
        track = pygame.Rect(bx, self.rect.y, self.SCROLLBAR_W, bh)
        pygame.draw.rect(surface, self.TRACK_COLOUR, track, border_radius=4)
        total  = max(len(self._items) * (self.row_height + self.row_gap), 1)
        ratio  = min(1.0, bh / total)
        th     = max(20, int(bh * ratio))
        ms     = self._max_scroll()
        pct    = self._scroll_y / ms if ms > 0 else 0.0
        ty     = self.rect.y + int((bh - th) * pct)
        colour = self.THUMB_HOVERED if self.hovered else self.THUMB_COLOUR
        pygame.draw.rect(surface, colour,
                         pygame.Rect(bx + 1, ty, self.SCROLLBAR_W - 2, th),
                         border_radius=4)