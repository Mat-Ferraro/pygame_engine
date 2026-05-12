"""
examples/example_buttons.py

Demonstrates Panel, Button, Label, and layout helpers working together.

What this example shows:
- A Panel containing a column of buttons
- Labels for title and status
- Hover, press, and disabled button states
- Clicking a button updates the status label
- Theme-driven colours throughout
- ESC or Quit exits cleanly

Run from the repo root:
    python -m examples.example_buttons
"""

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel


class ButtonExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._status_label: Label | None = None

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        theme = get_theme()

        # ── Main panel ────────────────────────────────────────────────────────
        panel_rect = anchor(screen, (320, 360), "center")
        panel = Panel(panel_rect)

        # ── Title label ───────────────────────────────────────────────────────
        title_rect = pygame.Rect(panel_rect.x, panel_rect.y - 56,
                                 panel_rect.width, 44)
        title = Label(title_rect, "Main Menu",
                      font_size=theme.typography.xl,
                      colour=theme.colours.text,
                      align="center")

        # ── Buttons inside the panel ──────────────────────────────────────────
        btn_rects = column(panel_rect, count=3,
                           item_size=(220, 52), spacing=14,
                           padding=theme.spacing.xl)

        btn_new  = Button(btn_rects[0], "New Game",
                          on_click=lambda: self._set_status("New Game clicked!"))
        btn_opts = Button(btn_rects[1], "Options",
                          on_click=lambda: self._set_status("Options clicked!"))
        btn_quit = Button(btn_rects[2], "Quit",
                          on_click=self._app.stop)

        panel.add(btn_new)
        panel.add(btn_opts)
        panel.add(btn_quit)

        # ── Disabled button (outside panel, bottom-right corner) ──────────────
        disabled_rect = anchor(screen, (200, 48), "bottom_right", margin=32)
        btn_disabled = Button(disabled_rect, "Unavailable")
        btn_disabled.enabled = False

        # ── Status label ──────────────────────────────────────────────────────
        status_rect = anchor(screen, (400, 34), "bottom", margin=48)
        self._status_label = Label(status_rect, "Click a button",
                                   font_size=theme.typography.sm,
                                   colour=theme.colours.text_secondary,
                                   align="center")

        # ── Hint label ────────────────────────────────────────────────────────
        hint_rect = anchor(screen, (300, 26), "bottom", margin=18)
        hint = Label(hint_rect, "ESC to quit",
                     font_size=theme.typography.xs,
                     colour=theme.colours.text_secondary,
                     align="center")

        # ── Root: a panel that holds everything ───────────────────────────────
        root = Panel(pygame.Rect(screen))
        root.visible = True

        # Panel has no background by default when used as an invisible root —
        # override by not drawing the background (we use root purely as a group)
        root._draw_background = lambda s: None  # type: ignore[method-assign]

        root.add(panel)
        root.add(title)
        root.add(btn_disabled)
        root.add(self._status_label)
        root.add(hint)

        self.root_widget = root

    def on_exit(self) -> None:
        print("[ButtonExampleScene] on_exit")

    def _set_status(self, message: str) -> None:
        if self._status_label:
            self._status_label.text = message

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def update(self, dt: float) -> None:
        pygame.display.set_caption(
            f"{self._app.config.title}  |  "
            f"FPS: {self._app.clock.get_fps():.0f}"
        )
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


def run() -> None:
    config = AppConfig(
        title="pygame_engine — panel & button example",
        width=1280,
        height=720,
        target_fps=60,
    )
    app = Application(config)
    app.run(ButtonExampleScene(app))


if __name__ == "__main__":
    run()
