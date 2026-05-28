"""
examples/example_buttons_described.py

A DescribedScene version of example_buttons. Use this with the scene editor:

    py -3.13 -m editor --scene examples.example_buttons_described.ButtonDescribedScene

What this demonstrates:
- The intended DescribedScene pattern: a subclass overrides ONLY
  ``_build_layout()`` (declare the UI as a descriptor) and, optionally,
  ``_bind_behavior()`` (attach callbacks to widgets by id). The base
  class handles realising the descriptor into a live widget tree, keeping
  widget geometry bound to the descriptor, and tearing the bindings down
  on exit.
- Because the base class binds each widget's rect to its descriptor node,
  editing geometry in the editor (inspector fields, drag gizmos) moves
  the actual widget — the binding is live.

Note: this scene does NOT override on_enter / on_exit / build its own
widgets. Earlier versions did, which fought the base class and broke the
editor's live editing. The engine already does build → load → realise →
bind for you; a scene just declares layout and wires behaviour.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene.described_scene import DescribedScene
import pygame_engine.scene.layout_builder  # noqa: F401 — patches builder()
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label
from pygame_engine.input import actions


class ButtonDescribedScene(DescribedScene):
    """
    Main-menu button layout as a DescribedScene.

    Overrides only ``_build_layout()`` and ``_bind_behavior()``. The base
    class realises the descriptor and keeps widget geometry bound to it.
    """

    @classmethod
    def editor_context(cls) -> dict:
        return {
            "title":  "Main Menu",
            "width":  1280,
            "height": 720,
        }

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app          = app
        self._status_label: Label | None = None

    # ── Layout descriptor ─────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Declare the widget tree in the SceneDescriptor.

        Font sizes / colours are carried as node props so the loader's
        Label builder reproduces the intended appearance.
        """
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)

        panel_rect    = anchor(screen, (320, 360), "center")
        title_rect    = pygame.Rect(panel_rect.x, panel_rect.y - 56,
                                    panel_rect.width, 44)
        disabled_rect = anchor(screen, (200, 48), "bottom_right", margin=32)
        status_rect   = anchor(screen, (400, 34), "bottom", margin=48)
        hint_rect     = anchor(screen, (300, 26), "bottom", margin=18)

        theme     = get_theme()
        btn_rects = column(panel_rect, count=3,
                           item_size=(220, 52), spacing=14,
                           padding=theme.spacing.xl)

        with self.layout.builder() as L:
            # Root container
            L.panel("root",
                    x=screen.x, y=screen.y, w=screen.w, h=screen.h)

            # Title
            L.label("title",
                    x=title_rect.x, y=title_rect.y,
                    w=title_rect.w, h=title_rect.h,
                    parent="root",
                    text="Main Menu",
                    align="center",
                    font_size=theme.typography.xl,
                    colour=list(theme.colours.text))

            # Main panel
            L.panel("main_panel",
                    x=panel_rect.x, y=panel_rect.y,
                    w=panel_rect.w, h=panel_rect.h,
                    parent="root")

            # Buttons inside main_panel
            L.button("btn_new_game",
                     x=btn_rects[0].x, y=btn_rects[0].y,
                     w=btn_rects[0].w, h=btn_rects[0].h,
                     parent="main_panel",
                     label="New Game")

            L.button("btn_options",
                     x=btn_rects[1].x, y=btn_rects[1].y,
                     w=btn_rects[1].w, h=btn_rects[1].h,
                     parent="main_panel",
                     label="Options")

            L.button("btn_quit",
                     x=btn_rects[2].x, y=btn_rects[2].y,
                     w=btn_rects[2].w, h=btn_rects[2].h,
                     parent="main_panel",
                     label="Quit")

            # Disabled button
            L.button("btn_disabled",
                     x=disabled_rect.x, y=disabled_rect.y,
                     w=disabled_rect.w, h=disabled_rect.h,
                     parent="root",
                     label="Unavailable")

            # Status label
            L.label("status_label",
                    x=status_rect.x, y=status_rect.y,
                    w=status_rect.w, h=status_rect.h,
                    parent="root",
                    text="Click a button",
                    align="center",
                    font_size=theme.typography.sm,
                    colour=list(theme.colours.text_secondary))

            # Hint label
            L.label("hint_label",
                    x=hint_rect.x, y=hint_rect.y,
                    w=hint_rect.w, h=hint_rect.h,
                    parent="root",
                    text="ESC to quit",
                    align="center",
                    font_size=theme.typography.xs,
                    colour=list(theme.colours.text_secondary))

    # ── Behaviour ──────────────────────────────────────────────────────────────

    def _bind_behavior(self) -> None:
        """
        Attach callbacks and per-instance state to the built widgets.

        Runs after the widget tree exists (and after every rebuild), so
        widgets are looked up by id via self.widget() / self.find_widget().
        """
        self.widget("btn_new_game").on_click = lambda: self._set_status("New Game clicked!")
        self.widget("btn_options").on_click  = lambda: self._set_status("Options clicked!")
        self.widget("btn_quit").on_click     = self._app.stop

        # The disabled button is a normal Button flagged not-enabled.
        self.widget("btn_disabled").enabled = False

        # The root Panel draws a themed background by default; the menu
        # wants the scene's own fill to show through. Suppress it. Note the
        # (surface, ctx) signature — Panel.render calls
        # self._draw_background(surface, ctx).
        root = self.find_widget("root")
        if root is not None:
            root._draw_background = lambda s, ctx: None  # type: ignore[method-assign]

        # Keep a handle to the status label so _set_status can update it.
        status = self.find_widget("status_label")
        if isinstance(status, Label):
            self._status_label = status

    # ── Scene behaviour ───────────────────────────────────────────────────────

    def _set_status(self, message: str) -> None:
        if self._status_label:
            self._status_label.text = message

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def update(self, dt: float) -> None:
        super().update(dt)

    def render(self, surface: pygame.Surface, ctx=None) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface, ctx)


def run() -> None:
    config = AppConfig(
        title="pygame_engine — buttons (described)",
        width=1280, height=720,
        resizable=True, target_fps=60,
    )
    app = Application(config)
    app.run(ButtonDescribedScene(app))


if __name__ == "__main__":
    run()
