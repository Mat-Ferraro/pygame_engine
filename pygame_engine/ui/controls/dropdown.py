"""
ui/controls/dropdown.py

Dropdown widget for pygame_engine.

A button that opens a floating list of selectable options. The list
renders above all other widgets via an ``overlay_render()`` call that
the owning scene or container makes last in its render pass.

Z-ordering
----------
Dropdowns cannot self-manage z-order because widgets render in the order
their parent renders them. The solution is a two-pass render:

1. Normal pass — ``render()`` draws the closed button face (always).
2. Overlay pass — ``overlay_render()`` draws the open list (when open).

In your scene::

    def render(self, surface):
        surface.fill(bg)
        super().render(surface)           # normal widget tree
        self._dropdown.overlay_render(surface)   # on top of everything

Usage::

    from pygame_engine.ui.controls.dropdown import Dropdown

    quality = Dropdown(
        rect=pygame.Rect(100, 200, 200, 42),
        options=["Low", "Medium", "High", "Ultra"],
        selected_index=1,
        on_change=lambda val, idx: apply_quality(val),
    )

    # Reading the selection:
    quality.selected_value   # "Medium"
    quality.selected_index   # 1
"""

from __future__ import annotations

from typing import Any, Callable

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget


class Dropdown(Widget):
    """
    Button that opens a floating option list.

    Selection
    ---------
    Options are a list of strings. Each option can optionally have an
    associated value (any type) via ``values``. If ``values`` is not
    supplied, the string labels are used as values.

    ``on_change(value, index)`` fires when the selection changes.

    Keyboard navigation
    -------------------
    When open, Up/Down arrows move the highlighted item.
    Enter or Space selects the highlighted item.
    Escape closes without changing selection.

    Overlay rendering
    -----------------
    Call ``overlay_render(surface)`` after all other rendering to draw
    the open list on top of everything else. It is a no-op when closed.
    """

    MAX_VISIBLE_ITEMS = 6   # scroll not implemented — capped at this count

    def __init__(
        self,
        rect:           pygame.Rect,
        options:        list[str],
        values:         list[Any] | None              = None,
        selected_index: int                            = 0,
        on_change:      Callable[[Any, int], None] | None = None,
        placeholder:    str                            = "Select...",
    ) -> None:
        """
        Args:
            rect:           Position and size of the closed button face.
            options:        Display strings for each option.
            values:         Parallel list of values. If None, options are used.
            selected_index: Initially selected index. -1 = no selection.
            on_change:      Called with (value, index) when selection changes.
            placeholder:    Text shown when selected_index is -1.
        """
        super().__init__(rect)

        if not options:
            raise ValueError("Dropdown requires at least one option.")
        if values is not None and len(values) != len(options):
            raise ValueError(
                f"values length ({len(values)}) must match "
                f"options length ({len(options)})."
            )

        self._options:    list[str]                     = list(options)
        self._values:     list[Any]                     = (
            list(values) if values is not None else list(options)
        )
        self._selected:   int                           = selected_index
        self._on_change:  Callable[[Any, int], None] | None = on_change
        self._placeholder: str                          = placeholder

        self._open:       bool = False
        self._hovered_item: int = -1   # index of item under cursor in list

        self._font: pygame.font.Font | None = None
        self._item_height: int = rect.height

        # Computed when opened
        self._list_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def selected_index(self) -> int:
        """Currently selected option index. -1 if nothing selected."""
        return self._selected

    @property
    def selected_value(self) -> Any:
        """The value of the currently selected option, or None."""
        if self._selected < 0 or self._selected >= len(self._values):
            return None
        return self._values[self._selected]

    @property
    def selected_label(self) -> str:
        """The display string of the currently selected option."""
        if self._selected < 0 or self._selected >= len(self._options):
            return self._placeholder
        return self._options[self._selected]

    @property
    def is_open(self) -> bool:
        """True when the option list is open."""
        return self._open

    def select(self, index: int) -> None:
        """
        Programmatically select an option by index.

        Fires ``on_change`` if the selection changed.
        """
        if index < 0 or index >= len(self._options):
            raise IndexError(f"Index {index} out of range for {len(self._options)} options.")
        if index != self._selected:
            self._selected = index
            self._fire_change()

    def close(self) -> None:
        """Close the dropdown list without changing selection."""
        self._open = False
        self._hovered_item = -1

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._open:
                # Click on a list item
                idx = self._item_at(event.pos)
                if idx >= 0:
                    self._select_and_close(idx)
                    return True
                # Click outside — close without selecting
                self.close()
                return False

            else:
                # Click on closed button face — open
                if self.rect.collidepoint(event.pos):
                    self._open_list()
                    return True

        if event.type == pygame.MOUSEMOTION and self._open:
            self._hovered_item = self._item_at(event.pos)

        if event.type == pygame.KEYDOWN and self._open:
            return self._handle_key(event)

        return False

    def _handle_key(self, event: pygame.event.Event) -> bool:
        visible = min(len(self._options), self.MAX_VISIBLE_ITEMS)

        if event.key == pygame.K_DOWN:
            self._hovered_item = min(
                self._hovered_item + 1, visible - 1
            )
            if self._hovered_item < 0:
                self._hovered_item = 0
            return True

        if event.key == pygame.K_UP:
            self._hovered_item = max(self._hovered_item - 1, 0)
            return True

        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self._hovered_item >= 0:
                self._select_and_close(self._hovered_item)
            return True

        if event.key == pygame.K_ESCAPE:
            self.close()
            return True

        return False

    # ── Normal render — closed button face ───────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        """Draw the closed button face. Always called in normal render order."""
        if not self.visible:
            return

        theme  = get_theme()
        font   = self._get_font(theme)
        style  = (theme.button.disabled if not self.enabled
                  else theme.button.hovered if self.hovered or self._open
                  else theme.button.normal)

        # Background + border
        pygame.draw.rect(surface, style.bg, self.rect,
                         border_radius=style.radius)
        if style.border_width > 0:
            pygame.draw.rect(surface, style.border, self.rect,
                             width=style.border_width,
                             border_radius=style.radius)

        # Label
        label_colour = (theme.button.text_disabled.colour
                        if not self.enabled else theme.button.text.colour)
        label_surf = font.render(self.selected_label, True, label_colour)
        lx = self.rect.x + 10
        ly = self.rect.centery - label_surf.get_height() // 2
        surface.blit(label_surf, (lx, ly))

        # Chevron indicator
        from pygame_engine.graphics.draw_utils import draw_chevron
        cx = self.rect.right - 16
        cy = self.rect.centery
        direction = "up" if self._open else "down"
        draw_chevron(surface, (cx, cy), 5, label_colour,
                     direction=direction, width=2)

    # ── Overlay render — open list ────────────────────────────────────────────

    def overlay_render(self, surface: pygame.Surface) -> None:
        """
        Draw the open option list.

        Call this LAST in your scene's render() — after super().render() —
        so the list appears above all other widgets.

        This is a no-op when the dropdown is closed.
        """
        if not self._open or not self.visible:
            return

        theme  = get_theme()
        font   = self._get_font(theme)
        r      = self._list_rect
        radius = theme.panel.surface.radius

        # List background
        pygame.draw.rect(surface, theme.colours.bg_raised, r,
                         border_radius=radius)
        pygame.draw.rect(surface, theme.colours.border, r,
                         width=1, border_radius=radius)

        # Items
        visible = min(len(self._options), self.MAX_VISIBLE_ITEMS)
        for i in range(visible):
            item_rect = pygame.Rect(
                r.x, r.y + i * self._item_height,
                r.width, self._item_height,
            )

            # Highlight
            if i == self._hovered_item:
                pygame.draw.rect(surface, theme.colours.bg_overlay,
                                 item_rect, border_radius=radius)
            elif i == self._selected:
                hl = pygame.Surface(item_rect.size, pygame.SRCALPHA)
                hl.fill((*theme.colours.border, 60))
                surface.blit(hl, item_rect.topleft)

            # Option text
            colour = (theme.colours.text
                      if i != self._selected
                      else theme.colours.text)
            text_surf = font.render(self._options[i], True, colour)
            tx = item_rect.x + 10
            ty = item_rect.centery - text_surf.get_height() // 2
            surface.blit(text_surf, (tx, ty))

        # Divider under selected hint
        pygame.draw.line(
            surface, theme.colours.border,
            (r.x + 4, r.y), (r.right - 4, r.y), 1
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _open_list(self) -> None:
        """Open the dropdown and compute the list rect."""
        self._open = True
        self._hovered_item = self._selected

        visible = min(len(self._options), self.MAX_VISIBLE_ITEMS)
        list_h  = visible * self._item_height

        # Try to open below; if it would go off-screen, open above
        screen_h = pygame.display.get_surface().get_height() \
                   if pygame.display.get_surface() else 10000
        if self.rect.bottom + list_h <= screen_h:
            list_y = self.rect.bottom
        else:
            list_y = self.rect.top - list_h

        self._list_rect = pygame.Rect(
            self.rect.x, list_y, self.rect.width, list_h
        )

    def _item_at(self, pos: tuple[int, int]) -> int:
        """Return the list item index at ``pos``, or -1 if none."""
        if not self._list_rect.collidepoint(pos):
            return -1
        relative_y = pos[1] - self._list_rect.y
        idx = relative_y // self._item_height
        visible = min(len(self._options), self.MAX_VISIBLE_ITEMS)
        if 0 <= idx < visible:
            return idx
        return -1

    def _select_and_close(self, index: int) -> None:
        changed = index != self._selected
        self._selected = index
        self.close()
        if changed:
            self._fire_change()

    def _fire_change(self) -> None:
        if self._on_change is not None:
            self._on_change(self.selected_value, self._selected)

    def _get_font(self, theme: object) -> pygame.font.Font:
        if self._font is None:
            from pygame_engine.theme.defaults import Theme
            t: Theme = theme  # type: ignore[assignment]
            self._font = pygame.font.SysFont(
                t.typography.family, t.typography.md
            )
        return self._font  # type: ignore[return-value]
