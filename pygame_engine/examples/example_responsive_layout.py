"""
Demonstrates responsive layout (FlexRow, FlexColumn, AnchorLayout).

What this example shows:
- AnchorLayout pinning widgets to screen edges
- FlexColumn distributing panels proportionally
- All layouts recompute when the window is resized
- Resize the window to see layouts adapt

Controls:
    R — simulate a resize to 800x500
    F — simulate a resize to 1920x1080
    ESC — quit

Run from the repo root:
    python -m examples.example_responsive_layout
"""

from __future__ import annotations
import pygame
from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import AnchorLayout, FlexColumn, FlexRow
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack


class ResponsiveScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app      = app
        self._anch:    AnchorLayout | None = None
        self._flex_col: FlexColumn | None = None
        self._top_bar:  Panel | None = None
        self._content:  Panel | None = None
        self._sidebar:  Panel | None = None
        self._status:   Label | None = None

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()

        # Top bar — always 48px tall, full width
        # Main area — split: sidebar 220px fixed, content fills rest
        # Status bar — always 32px tall, full width
        self._flex_col = FlexColumn(spacing=2)

        top_bar = Panel(pygame.Rect(screen))
        content_row_rect = pygame.Rect(screen)
        status_bar = Panel(pygame.Rect(screen))

        self._flex_col.add(top_bar,       fixed=48)
        self._flex_col.add(content_row_rect, weight=1)  # placeholder — we'll split below
        self._flex_col.add(status_bar,    fixed=32)
        rects = self._flex_col.layout(screen)

        # Split middle row: sidebar + content
        flex_row = FlexRow(spacing=2)
        sidebar  = Panel(rects[1])
        content  = Panel(rects[1])
        flex_row.add(sidebar, fixed=220)
        flex_row.add(content, weight=1)
        row_rects = flex_row.layout(rects[1])
        sidebar.set_rect(row_rects[0])
        content.set_rect(row_rects[1])

        # Add labels
        def _lbl(rect, text, size=None):
            theme_ = get_theme()
            return Label(rect, text,
                         font_size=size or theme_.typography.sm,
                         colour=theme_.colours.text_secondary,
                         align="center")

        top_bar.add(_lbl(rects[0], "Top Bar — full width, 48px fixed",
                         theme.typography.md))
        sidebar.add(_lbl(row_rects[0], "Sidebar\n220px fixed"))
        content.add(_lbl(row_rects[1], "Main content area\nfills remaining width"))
        status_bar.add(_lbl(rects[2], "Status bar — full width, 32px fixed",
                            theme.typography.xs))

        # AnchorLayout for corner widgets
        anch = AnchorLayout()
        help_lbl = Label(pygame.Rect(0,0,380,20), "",
                         font_size=theme.typography.xs,
                         colour=theme.colours.text_secondary)
        anch.add(help_lbl, "bottom_right", size=(380, 20), margin=40)
        help_lbl.text = "R=800x500  F=1920x1080  ESC=quit"
        anch.apply(screen)

        self._status = Label(pygame.Rect(0,0,500,20), "",
                             font_size=theme.typography.xs,
                             colour=theme.colours.text_secondary,
                             align="center")
        anch.add(self._status, "bottom", size=(500, 20), margin=10)
        self._status.text = f"Window: {screen.width}×{screen.height}"
        anch.apply(screen)

        root = Stack(pygame.Rect(screen))
        root.add(top_bar)
        root.add(sidebar)
        root.add(content)
        root.add(status_bar)
        root.add(help_lbl)
        root.add(self._status)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        from pygame_engine.input import actions
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._build_ui(pygame.Rect(0, 0, 800, 500)); return True
            if event.key == pygame.K_f:
                self._build_ui(pygame.Rect(0, 0, 1920, 1080)); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((15, 15, 22))
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(title="pygame_engine — responsive layout",
                                width=1280, height=720, resizable=True))
    app.run(ResponsiveScene(app))

if __name__ == "__main__":
    run()
