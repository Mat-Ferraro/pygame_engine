"""
Demonstrates responsive layout: AnchorLayout, FlexRow, FlexColumn.

What this example shows:
- FlexColumn distributing panels into fixed-height top/bottom bars and
  a weighted middle area
- FlexRow splitting the middle into a fixed sidebar and a weighted
  content area
- AnchorLayout pinning labels to screen corners
- All layouts recompute when the window is resized (drag the edge)
- Simulated resize via R and F keys

Controls:
    R       — resize to 800×500
    F       — resize to 1920×1080
    Drag    — resize window freely (resizable=True)
    ESC     — quit

Run from the repo root:
    python -m examples.example_responsive_layout
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import AnchorLayout, FlexColumn, FlexRow
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Panel, Stack
from pygame_engine.input import actions


class ResponsiveScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._status: Label | None = None

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()

        # ── Step 1: FlexColumn divides the screen top-to-bottom ───────────────
        # We use dummy sentinel objects so FlexColumn can call set_rect,
        # then we read back the computed rects.
        class _RectHolder:
            def __init__(self): self.rect = pygame.Rect(0,0,0,0)
            def set_rect(self, r): self.rect = r

        col_top    = _RectHolder()
        col_middle = _RectHolder()
        col_bottom = _RectHolder()

        flex_col = FlexColumn(spacing=2)
        flex_col.add(col_top,    fixed=48)
        flex_col.add(col_middle, weight=1)
        flex_col.add(col_bottom, fixed=32)
        flex_col.layout(screen)

        # ── Step 2: FlexRow divides the middle row left-to-right ──────────────
        row_sidebar = _RectHolder()
        row_content = _RectHolder()

        flex_row = FlexRow(spacing=2)
        flex_row.add(row_sidebar, fixed=220)
        flex_row.add(row_content, weight=1)
        flex_row.layout(col_middle.rect)

        # ── Step 3: Build actual panels at the computed rects ─────────────────
        def panel_with_label(rect: pygame.Rect, text: str,
                             size: int | None = None) -> Panel:
            p = Panel(rect)
            p.add(Label(
                pygame.Rect(rect.x + 8, rect.y, rect.width - 16, rect.height),
                text,
                font_size=size or theme.typography.sm,
                colour=theme.colours.text_secondary,
                align="center",
            ))
            return p

        top_bar   = panel_with_label(col_top.rect,
                                     "Top bar — 48 px fixed, full width",
                                     theme.typography.md)
        sidebar   = panel_with_label(row_sidebar.rect,
                                     "Sidebar\n220 px fixed")
        content   = panel_with_label(row_content.rect,
                                     "Main content — weighted, fills remaining width")
        status_bar = panel_with_label(col_bottom.rect,
                                      "Status bar — 32 px fixed, full width",
                                      theme.typography.xs)

        # ── Step 4: AnchorLayout for corner hints ─────────────────────────────
        anch = AnchorLayout()

        # Hint — bottom right, one line
        hint = Label(pygame.Rect(0, 0, 520, 20), "",
                     font_size=theme.typography.xs,
                     colour=theme.colours.text_secondary,
                     align="right")
        hint.text = "R = 800×500   F = 1920×1080   drag edge   ESC = quit"
        anch.add(hint, "bottom_right", size=(520, 20), margin=8)

        # Status — bottom left, shows current window size
        self._status = Label(pygame.Rect(0, 0, 260, 20), "",
                             font_size=theme.typography.xs,
                             colour=theme.colours.text_secondary,
                             align="left")
        self._status.text = f"Window: {screen.width} × {screen.height}"
        anch.add(self._status, "bottom_left", size=(260, 20), margin=8)

        anch.apply(screen)

        # ── Root ──────────────────────────────────────────────────────────────
        root = Stack(pygame.Rect(screen))
        root.add(top_bar)
        root.add(sidebar)
        root.add(content)
        root.add(status_bar)
        root.add(hint)
        root.add(self._status)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._build_ui(pygame.Rect(0, 0, 800, 500)); return True
            if event.key == pygame.K_f:
                self._build_ui(pygame.Rect(0, 0, 1920, 1080)); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_dark)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — responsive layout",
        width=1280, height=720,
        resizable=True,
    ))
    app.run(ResponsiveScene(app))


if __name__ == "__main__":
    run()
