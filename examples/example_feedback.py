"""
examples/example_feedback.py

Demonstrates Toast and Tooltip feedback widgets.

What this example shows:
- Three buttons, each triggering a differently styled toast
- A tooltip that follows the mouse when hovering any button
- Toast auto-dismiss with fade in/out
- Manual toast dismiss on ESC

Run from the repo root:
    python -m examples.example_feedback
"""

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Toast, Tooltip
from pygame_engine.ui.containers.stack import Stack


class FeedbackExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app     = app
        self._toast:   Toast | None   = None
        self._tooltip: Tooltip | None = None
        self._buttons: list[Button]   = []

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        theme = get_theme()

        # ── Panel with three buttons ──────────────────────────────────────────
        panel_rect = anchor(screen, (300, 300), "center")
        panel = Panel(panel_rect)

        btn_rects = column(panel_rect, count=3,
                           item_size=(220, 52), spacing=14,
                           padding=theme.spacing.xl)

        labels_and_kinds = [
            ("Save Game",    "success"),
            ("Load Warning", "warning"),
            ("Delete Save",  "error"),
        ]

        self._buttons = []
        for rect, (lbl, kind) in zip(btn_rects, labels_and_kinds):
            k = kind  # capture for lambda
            btn = Button(rect, lbl,
                         on_click=lambda k=k, l=lbl: self._show_toast(l, k))
            panel.add(btn)
            self._buttons.append(btn)

        # ── Title ─────────────────────────────────────────────────────────────
        title_rect = pygame.Rect(panel_rect.x, panel_rect.y - 56,
                                 panel_rect.width, 44)
        title = Label(title_rect, "Feedback Widgets",
                      font_size=theme.typography.xl,
                      colour=theme.colours.text,
                      align="center")

        # ── Hint ──────────────────────────────────────────────────────────────
        hint_rect = anchor(screen, (400, 28), "bottom", margin=18)
        hint = Label(hint_rect, "Hover buttons for tooltips  •  ESC to quit",
                     font_size=theme.typography.xs,
                     colour=theme.colours.text_secondary,
                     align="center")

        # ── Toast (initially hidden, positioned bottom-centre) ────────────────
        self._toast = Toast("", duration=2.5)
        toast_rect = anchor(screen, (280, 52), "bottom", margin=60)
        self._toast.set_rect(toast_rect)

        # ── Tooltip ───────────────────────────────────────────────────────────
        self._tooltip = Tooltip(screen, "Click to trigger a notification")

        # ── Root ──────────────────────────────────────────────────────────────
        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        root.add(hint)
        # Toast and tooltip are NOT added to root — we update/render them
        # manually so they always draw on top of everything else.

        self.root_widget = root

    def on_exit(self) -> None:
        print("[FeedbackExampleScene] on_exit")

    def _show_toast(self, message: str, kind: str) -> None:
        if self._toast:
            self._toast.text = message
            self._toast._kind = kind
            self._toast._dirty = True
            self._toast.show()

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            if self._toast and self._toast.is_active:
                self._toast.dismiss()
            else:
                self._app.stop()
            return True
        return False

    def update(self, dt: float) -> None:
        pygame.display.set_caption(
            f"{self._app.config.title}  |  "
            f"FPS: {self._app.clock.get_fps():.0f}"
        )
        super().update(dt)

        # Update toast
        if self._toast:
            self._toast.update(dt)

        # Update tooltip — show if any button is hovered
        if self._tooltip:
            mouse_pos = self._app.input_manager.get_mouse_pos()
            any_hovered = any(b.hovered for b in self._buttons)
            if any_hovered:
                self._tooltip.show(mouse_pos)
            else:
                self._tooltip.hide()
            self._tooltip.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)

        # Toast and tooltip render last so they appear above all other widgets
        if self._toast:
            self._toast.render(surface)
        if self._tooltip:
            self._tooltip.render(surface)


def run() -> None:
    config = AppConfig(
        title="pygame_engine — feedback example",
        width=1280,
        height=720,
        target_fps=60,
    )
    app = Application(config)
    app.run(FeedbackExampleScene(app))


if __name__ == "__main__":
    run()
