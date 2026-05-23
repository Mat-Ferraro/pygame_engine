"""
examples/example_buttons_described.py

A DescribedScene version of example_buttons. Use this with the scene editor:

    py -3.13 -m editor --scene examples.example_buttons_described.ButtonDescribedScene

What this demonstrates:
- How to migrate a regular Scene to DescribedScene
- The layout descriptor populating the hierarchy panel
- Widget nodes visible and selectable in the editor
- The scene still runs identically as a standalone example

The actual widget construction reads from the SceneDescriptor, so the
editor can inspect and eventually edit the layout live.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene.described_scene import DescribedScene
import pygame_engine.scene.layout_builder  # noqa: F401 — patches builder()
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel
from pygame_engine.input import actions


class ButtonDescribedScene(DescribedScene):
    """
    Main-menu button layout as a DescribedScene.

    The descriptor is built in _build_layout() using the Layout DSL.
    on_enter() reads from the descriptor to construct actual pygame widgets.
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
        """Declare the widget tree in the SceneDescriptor."""
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
                    align="center")

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
                    align="center")

            # Hint label
            L.label("hint_label",
                    x=hint_rect.x, y=hint_rect.y,
                    w=hint_rect.w, h=hint_rect.h,
                    parent="root",
                    text="ESC to quit",
                    align="center")

    # ── Widget construction from descriptor ───────────────────────────────────

    def on_enter(self) -> None:
        super().on_enter()   # calls _build_layout()
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Instantiate real pygame widgets from the descriptor nodes."""
        theme = get_theme()

        def r(node_id: str) -> pygame.Rect:
            """Get a pygame.Rect from a descriptor node."""
            node = self.layout.get(node_id)
            return node.rect.to_pygame_rect()

        def prop(node_id: str, key: str, default="") -> str:
            """Get a prop value from a descriptor node."""
            node = self.layout.get(node_id)
            obs  = node.props.get(key)
            return obs.value if obs is not None else default

        # Root
        root = Panel(r("root"))
        root._draw_background = lambda s: None  # type: ignore[method-assign]

        # Title
        title = Label(r("title"),
                      prop("title", "text", "Main Menu"),
                      font_size=theme.typography.xl,
                      colour=theme.colours.text,
                      align=prop("title", "align", "center"))

        # Main panel
        main_panel = Panel(r("main_panel"))

        # Buttons
        btn_new = Button(r("btn_new_game"),
                         prop("btn_new_game", "label", "New Game"),
                         on_click=lambda: self._set_status("New Game clicked!"))

        btn_opts = Button(r("btn_options"),
                          prop("btn_options", "label", "Options"),
                          on_click=lambda: self._set_status("Options clicked!"))

        btn_quit = Button(r("btn_quit"),
                          prop("btn_quit", "label", "Quit"),
                          on_click=self._app.stop)

        main_panel.add(btn_new)
        main_panel.add(btn_opts)
        main_panel.add(btn_quit)

        # Disabled button
        btn_disabled = Button(r("btn_disabled"),
                              prop("btn_disabled", "label", "Unavailable"))
        btn_disabled.enabled = False

        # Status label
        self._status_label = Label(r("status_label"),
                                   prop("status_label", "text", "Click a button"),
                                   font_size=theme.typography.sm,
                                   colour=theme.colours.text_secondary,
                                   align=prop("status_label", "align", "center"))

        # Hint label
        hint = Label(r("hint_label"),
                     prop("hint_label", "text", "ESC to quit"),
                     font_size=theme.typography.xs,
                     colour=theme.colours.text_secondary,
                     align="center")

        root.add(main_panel)
        root.add(title)
        root.add(btn_disabled)
        root.add(self._status_label)
        root.add(hint)

        self.root_widget = root

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
