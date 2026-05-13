"""
Demonstrates Scrollable container and TextBlock widget.

What this example shows:
- Scrollable with a long TextBlock child
- Mouse wheel scrolling
- Scroll-to-top / scroll-to-bottom buttons
- TextBlock text wrapping and line spacing
- Multiple font sizes in adjacent panels

Controls:
    Mouse wheel — scroll
    Home / End  — scroll to top / bottom
    ESC         — quit

Run from the repo root:
    python -m examples.example_scrollable
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.ui.containers.scrollable import Scrollable
from pygame_engine.ui.text.text_block import TextBlock

LONG_TEXT = """\
pygame_engine is a lightweight, reusable pygame-ce framework for 2D games.

It provides a clean scene system, a full UI toolkit with 15 widgets, \
layout helpers, a theme system, input abstraction, assets, audio, animation, \
particles, camera, tilemap, dialogue, pathfinding, 2D lighting, localisation, \
key remapping, controller support, file-driven theming, and rich text — \
all in one cohesive package.

The Scrollable widget clips its child to a viewport rectangle and routes \
mouse wheel events to shift the scroll offset. It is designed to hold a \
single tall child widget, typically a TextBlock or a Panel containing a list \
of items.

The TextBlock widget wraps text across multiple lines respecting the widget \
width, using configurable padding and line spacing. It caches the rendered \
text surface and only rebuilds when the text or layout changes.

Together they form the foundation for any scrollable content area: patch notes, \
item descriptions, log viewers, credits screens, and configuration panels.

This example demonstrates both widgets working together. The scroll position \
is controlled by the mouse wheel, and two buttons let you jump to the top or \
bottom of the content instantly.

You can also use keyboard shortcuts: Home scrolls to the top and End scrolls \
to the bottom of the content.

The layout is built using the anchor() helper for positioning and the column() \
helper for the button group on the right.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor \
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis \
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu \
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in \
culpa qui officia deserunt mollit anim id est laborum.

End of scrollable content.
"""


class ScrollableExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app       = app
        self._scrollable: Scrollable | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        # ── Left panel: scrollable text ───────────────────────────────────────
        panel_rect = pygame.Rect(60, 60, 860, screen.height - 120)
        panel      = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 12,
                        panel_rect.width - 32, 28),
            "Scrollable TextBlock",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        viewport = pygame.Rect(
            panel_rect.x + 12, panel_rect.y + 52,
            panel_rect.width - 24, panel_rect.height - 64,
        )
        self._scrollable = Scrollable(viewport)

        content = TextBlock(
            pygame.Rect(0, 0, viewport.width - 4, 2000),
            LONG_TEXT,
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            padding=8,
            line_spacing=4,
        )
        self._scrollable.child = content

        # ── Right panel: controls ─────────────────────────────────────────────
        ctrl_rect  = pygame.Rect(940, 60, 280, screen.height - 120)
        ctrl_panel = Panel(ctrl_rect)

        ctrl_panel.add(Label(
            pygame.Rect(ctrl_rect.x + 16, ctrl_rect.y + 12,
                        ctrl_rect.width - 32, 28),
            "Controls",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        btn_rects = column(ctrl_rect, count=3, item_size=(220, 44),
                           spacing=10, padding=theme.spacing.xxl)
        ctrl_panel.add(Button(btn_rects[0], "Scroll to Top",
                               on_click=self._scroll_top))
        ctrl_panel.add(Button(btn_rects[1], "Scroll to Bottom",
                               on_click=self._scroll_bottom))
        ctrl_panel.add(Button(btn_rects[2], "Quit",
                               on_click=self._app.stop))

        # Hint
        hint_lines = [
            "Mouse wheel — scroll",
            "Home — top",
            "End — bottom",
        ]
        for i, hint in enumerate(hint_lines):
            ctrl_panel.add(Label(
                pygame.Rect(ctrl_rect.x + 16,
                             ctrl_rect.bottom - 90 + i * 22,
                             ctrl_rect.width - 32, 20),
                hint,
                font_size=theme.typography.xs,
                colour=theme.colours.text_secondary,
            ))

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(ctrl_panel)
        root.add(self._scrollable)
        self.root_widget = root

    def _scroll_top(self) -> None:
        if self._scrollable:
            self._scrollable.scroll_to_top()

    def _scroll_bottom(self) -> None:
        if self._scrollable:
            self._scrollable.scroll_to_bottom()

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_HOME:
                self._scroll_top(); return True
            if event.key == pygame.K_END:
                self._scroll_bottom(); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — scrollable & textblock",
        width=1280, height=720,
        resizable=True,
    ))
    app.run(ScrollableExampleScene(app))


if __name__ == "__main__":
    run()
