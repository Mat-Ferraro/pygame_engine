"""
examples/example_buttons.py

Demonstrates Button, Label, and layout helpers working together.

What this example shows:
- A column of three buttons laid out with column()
- A label at the top and a status label at the bottom
- Buttons respond to hover, press, and click
- One button is disabled
- Clicking a button updates the status label
- ESC quits via the action system

Run from the repo root:
    python -m examples.example_buttons
"""

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.ui import Button, Label
from pygame_engine.ui.base.widget import Widget


# ── A simple container to hold and delegate to multiple widgets ───────────────

class WidgetGroup(Widget):
    """
    Minimal non-layout container — holds a flat list of widgets and
    delegates the three frame methods to each in order.

    This is a lightweight stand-in until Panel is written. It does not
    clip or manage layout — callers assign rects externally.
    """

    def __init__(self) -> None:
        super().__init__(pygame.Rect(0, 0, 0, 0))
        self._children: list[Widget] = []

    def add(self, widget: Widget) -> None:
        self._children.append(widget)

    def _handle_event_widget(self, event: pygame.event.Event) -> bool:
        for child in reversed(self._children):
            if child.handle_event(event):
                return True
        return False

    def update(self, dt: float) -> None:
        for child in self._children:
            if child.visible:
                child.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        for child in self._children:
            child.render(surface)


# ── Scene ─────────────────────────────────────────────────────────────────────

class ButtonExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)

        group = WidgetGroup()

        # ── Title label ───────────────────────────────────────────────────────
        title_rect = anchor(screen, (400, 50), "top", margin=60)
        title = Label(title_rect, "Button Example", font_size=28,
                      colour=(220, 220, 220), align="center")
        group.add(title)

        # ── Three buttons in a centred column ─────────────────────────────────
        btn_rects = column(screen, count=3, item_size=(220, 52), spacing=16)

        self._status_text = "Click a button"

        btn_new = Button(btn_rects[0], "New Game",
                         on_click=lambda: self._set_status("New Game clicked!"))
        btn_opts = Button(btn_rects[1], "Options",
                          on_click=lambda: self._set_status("Options clicked!"))
        btn_quit = Button(btn_rects[2], "Quit",
                          on_click=self._app.stop)

        group.add(btn_new)
        group.add(btn_opts)
        group.add(btn_quit)

        # ── Disabled button example ───────────────────────────────────────────
        disabled_rect = anchor(screen, (220, 52), "bottom_right", margin=40)
        btn_disabled = Button(disabled_rect, "Unavailable")
        btn_disabled.enabled = False
        group.add(btn_disabled)

        # ── Status label ──────────────────────────────────────────────────────
        status_rect = anchor(screen, (400, 36), "bottom", margin=40)
        self._status_label = Label(status_rect, self._status_text,
                                   font_size=18, colour=(160, 200, 160),
                                   align="center")
        group.add(self._status_label)

        # ── Hint label ────────────────────────────────────────────────────────
        hint_rect = anchor(screen, (300, 28), "bottom", margin=16)
        hint = Label(hint_rect, "ESC to quit", font_size=16,
                     colour=(120, 120, 130), align="center")
        group.add(hint)

        self.root_widget = group

    def on_exit(self) -> None:
        print("[ButtonExampleScene] on_exit")

    def _set_status(self, message: str) -> None:
        self._status_text = message
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
        surface.fill((22, 22, 30))
        super().render(surface)


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    config = AppConfig(
        title="pygame_engine — button example",
        width=1280,
        height=720,
        target_fps=60,
    )
    app = Application(config)
    app.run(ButtonExampleScene(app))


if __name__ == "__main__":
    run()
