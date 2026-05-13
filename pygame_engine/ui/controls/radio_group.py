"""
RadioGroup widget for pygame_engine.

A group of mutually exclusive options. Selecting one deselects all others.
Reads visual style from the active theme.

Usage::

    from pygame_engine.ui.controls.radio_group import RadioGroup

    quality = RadioGroup(
        rect=pygame.Rect(100, 200, 200, 120),
        options=["Low", "Medium", "High"],
        selected_index=1,
        on_change=lambda i, v: apply_quality(v),
    )
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.base.widget import Widget
from pygame_engine.utils.mathx import clamp


class RadioGroup(Widget):
    """
    A vertical stack of mutually exclusive radio options.

    Each option shows a radio button (circle) with a text label. Only one
    option can be selected at a time. Keyboard: Up/Down navigates when
    focused; Space or Enter selects.

    Args:
        rect:           Position and size. Height is divided evenly among options.
        options:        List of label strings.
        selected_index: Initially selected option index. -1 = none selected.
        on_change:      Called with (index, label) when selection changes.
    """

    DOT_R  = 8    # outer circle radius
    FILL_R = 4    # inner filled dot radius when selected

    def __init__(
        self,
        rect:           pygame.Rect,
        options:        list[str],
        selected_index: int = 0,
        on_change:      Callable[[int, str], None] | None = None,
    ) -> None:
        if not options:
            raise ValueError("RadioGroup requires at least one option.")
        super().__init__(rect)
        self._options  = list(options)
        self._selected = clamp(selected_index, -1, len(options) - 1)
        self.on_change = on_change
        self.focusable = True
        self._font: pygame.font.Font | None = None
        self._focused_index: int = max(0, self._selected)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def selected_index(self) -> int:
        return self._selected

    @property
    def selected_value(self) -> str | None:
        if self._selected < 0:
            return None
        return self._options[self._selected]

    @property
    def options(self) -> list[str]:
        return list(self._options)

    def select(self, index: int) -> None:
        """Select an option by index. Fires on_change."""
        index = clamp(index, 0, len(self._options) - 1)
        if index != self._selected:
            self._selected = index
            self._focused_index = index
            if self.on_change:
                self.on_change(self._selected, self._options[self._selected])

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self._index_at(event.pos)
            if hit >= 0:
                self.select(hit)
                return True

        if event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_UP, pygame.K_LEFT):
                self._focused_index = max(0, self._focused_index - 1)
                return True
            if event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                self._focused_index = min(len(self._options) - 1, self._focused_index + 1)
                return True
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.select(self._focused_index)
                return True

        return False

    def _index_at(self, pos: tuple[int, int]) -> int:
        row_h = self._row_height()
        if not self.rect.collidepoint(pos):
            return -1
        rel_y = pos[1] - self.rect.y
        return min(int(rel_y // row_h), len(self._options) - 1)

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        theme   = get_theme()
        colours = theme.colours
        row_h   = self._row_height()

        if self._font is None:
            self._font = pygame.font.SysFont(
                theme.typography.family, theme.typography.md
            )

        for i, option in enumerate(self._options):
            cy = int(self.rect.y + row_h * i + row_h / 2)
            cx = self.rect.x + self.DOT_R + 2

            selected  = (i == self._selected)
            nav_focus = (self.focused and i == self._focused_index)

            # Outer ring
            border_col = (theme.button.hovered.border if nav_focus
                          else colours.border)
            pygame.draw.circle(surface, colours.bg_raised, (cx, cy), self.DOT_R)
            pygame.draw.circle(surface, border_col, (cx, cy), self.DOT_R, width=1)

            # Inner dot
            if selected:
                pygame.draw.circle(surface, theme.button.normal.bg,
                                   (cx, cy), self.FILL_R)

            # Focus ring on keyboard-navigated item
            if nav_focus and self.enabled:
                pygame.draw.circle(surface, colours.border_focus,
                                   (cx, cy), self.DOT_R + 3, width=2)

            # Label
            col  = (colours.text if self.enabled
                    else theme.button.text_disabled.colour)
            text = self._font.render(option, True, col)
            surface.blit(text, (cx + self.DOT_R + 8,
                                cy - text.get_height() // 2))

    def _row_height(self) -> float:
        return self.rect.height / len(self._options)
