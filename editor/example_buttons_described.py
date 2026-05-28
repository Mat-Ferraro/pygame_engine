"""
examples/example_buttons_described.py

A DescribedScene version of example_buttons. Use this with the scene editor:

    py -3.13 -m editor --scene examples.example_buttons_described.ButtonDescribedScene

What this demonstrates:
- How to migrate a regular Scene to DescribedScene the *intended* way:
  the descriptor is the source of truth, and ``LayoutLoader`` realises it
  into a live widget tree whose geometry stays bound to the descriptor.
- Because the loader subscribes each widget's rect to its node's rect,
  editing geometry in the editor (inspector fields, drag gizmos) moves
  the actual widget — not just the selection outline.
- Behaviour (button on_click, etc.) is attached after loading by
  widget_id, since the descriptor only carries structure + geometry.

Previously this example built widgets by hand from one-time rect
snapshots, which meant editor edits updated the descriptor but never the
live widgets. Using LayoutLoader is both the correct engine pattern and
what makes the editor's live editing work.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.scene.layout_loader import LayoutLoader
import pygame_engine.scene.layout_builder  # noqa: F401 — patches builder()
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label
from pygame_engine.input import actions


class ButtonDescribedScene(DescribedScene):
    """
    Main-menu button layout as a DescribedScene.

    The descriptor is built in ``_build_layout()`` using the Layout DSL.
    ``on_enter()`` realises it via ``LayoutLoader``, which keeps each
    widget's geometry bound to its descriptor node — the live binding the
    editor relies on. Behaviour is wired in ``_bind_behavior()`` by id.
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

        Font sizes / colours that used to be passed directly to the
        hand-built widgets are now carried as node props, so the loader's
        Label builder reproduces the same appearance.
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

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def on_enter(self) -> None:
        # super().on_enter() runs _build_layout() to populate the descriptor.
        super().on_enter()

        # Realise the descriptor into a live, rect-bound widget tree.
        self._loaded = LayoutLoader().load(self.layout)
        self.root_widget = self._loaded.root

        # The root Panel draws a themed background by default; the menu
        # wants the scene's own fill to show through. Suppress it. Note
        # the (surface, ctx) signature — Panel.render calls
        # self._draw_background(surface, ctx).
        root_widget = self._loaded.find("root")
        if root_widget is not None:
            root_widget._draw_background = lambda s, ctx: None  # type: ignore[method-assign]

        self._bind_behavior()

    def _bind_behavior(self) -> None:
        """Attach callbacks and per-instance state to the loaded widgets."""
        loaded = self._loaded

        loaded.by_id("btn_new_game").on_click = lambda: self._set_status("New Game clicked!")
        loaded.by_id("btn_options").on_click  = lambda: self._set_status("Options clicked!")
        loaded.by_id("btn_quit").on_click     = self._app.stop

        # The disabled button is a normal Button flagged not-enabled.
        loaded.by_id("btn_disabled").enabled = False

        # Keep a handle to the status label so _set_status can update it.
        status = loaded.find("status_label")
        if isinstance(status, Label):
            self._status_label = status

    def on_exit(self) -> None:
        # Release the live rect subscriptions created by the loader.
        loaded = getattr(self, "_loaded", None)
        if loaded is not None:
            loaded.dispose()
        super().on_exit()

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
