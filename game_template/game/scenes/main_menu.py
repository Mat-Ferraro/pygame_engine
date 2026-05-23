"""Main menu — Start, Settings, Quit with ConfirmDialog on quit.

Migrated to ``DescribedScene``: the UI is authored as a ``SceneDescriptor``
(structure + geometry in ``_build_layout()``), and behaviour — the button
callbacks — is attached in ``_bind_behavior()`` by widget id. The engine
realises the descriptor into the live widget tree; this scene never
constructs a widget directly.

This is the proving scene for the descriptor-authority model
(see docs/SPRINT_descriptor_authority.md).
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import FadeTransition, SlideTransition
from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.scene import layout_builder  # noqa: F401  (patches builder())
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui.controls.button import Button

from game import actions
from game.locale import t


class MainMenuScene(DescribedScene):
    """
    Main menu — Start, Settings, Quit.

    Demonstrates the descriptor-authored pattern:
    - ``_build_layout()`` declares the widget tree as descriptor nodes,
      computing geometry against ``self.screen_rect`` so it re-flows on
      resize.
    - ``_bind_behavior()`` wires the three buttons to their callbacks.
    - Localisation via ``t()`` for all user-visible strings.
    - Scene transitions on navigation; ConfirmDialog on quit.
    """

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Declare the menu's widget tree as descriptor nodes.

        Geometry is computed against ``self.screen_rect`` via the layout
        helpers, and the resulting literal rects are stored on the nodes —
        so a resize (which re-runs this method) re-flows the menu.
        """
        theme  = get_theme()
        screen = self.screen_rect

        # Title — anchored to the top.
        title_rect = anchor(screen, (500, 60), "top", margin=80)

        # Centre panel holding the three menu buttons.
        panel_rect = anchor(screen, (280, 240), "center", offset=(0, 30))

        # Three evenly spaced button rects inside the panel.
        btn_rects = column(
            panel_rect, count=3,
            item_size=(200, 52), spacing=14,
            padding=theme.spacing.xl,
        )

        # Version label — bottom-right corner.
        version_rect = anchor(screen, (200, 24), "bottom_right", margin=12)

        with self.layout.builder() as L:
            # Transparent root spanning the whole screen.
            L.stack("root", x=0, y=0, w=screen.w, h=screen.h)

            L.label(
                "title_lbl",
                x=title_rect.x, y=title_rect.y,
                w=title_rect.w, h=title_rect.h,
                parent="root",
                text=self._app.config.title,
                font_size=theme.typography.xxl,
                colour=list(theme.colours.text),
                align="center",
            )

            L.panel(
                "menu_panel",
                x=panel_rect.x, y=panel_rect.y,
                w=panel_rect.w, h=panel_rect.h,
                parent="root",
            )

            L.button(
                "start_btn",
                x=btn_rects[0].x, y=btn_rects[0].y,
                w=btn_rects[0].w, h=btn_rects[0].h,
                parent="menu_panel",
                label=t("menu.start"),
            )
            L.button(
                "settings_btn",
                x=btn_rects[1].x, y=btn_rects[1].y,
                w=btn_rects[1].w, h=btn_rects[1].h,
                parent="menu_panel",
                label=t("menu.settings"),
            )
            L.button(
                "quit_btn",
                x=btn_rects[2].x, y=btn_rects[2].y,
                w=btn_rects[2].w, h=btn_rects[2].h,
                parent="menu_panel",
                label=t("menu.quit"),
            )

            L.label(
                "version_lbl",
                x=version_rect.x, y=version_rect.y,
                w=version_rect.w, h=version_rect.h,
                parent="root",
                text="v1.3.0",
                font_size=theme.typography.xs,
                colour=list(theme.colours.text_secondary),
                align="right",
            )

    # ── Behaviour ─────────────────────────────────────────────────────────────

    def _bind_behavior(self) -> None:
        """Wire the three menu buttons to their navigation callbacks."""
        start = self.widget("start_btn")
        if isinstance(start, Button):
            start.on_click = self._on_start

        settings = self.widget("settings_btn")
        if isinstance(settings, Button):
            settings.on_click = self._on_settings

        quit_btn = self.widget("quit_btn")
        if isinstance(quit_btn, Button):
            quit_btn.on_click = self._on_quit

    # ── Frame methods ─────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._on_quit()
            return True
        return False

    def update(self, dt: float) -> None:
        pygame.display.set_caption(
            f"{self._app.config.title}  —  "
            f"{self._app.clock.get_fps():.0f} fps"
        )
        super().update(dt)

    def render(self, surface: pygame.Surface, ctx) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface, ctx)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_start(self) -> None:
        from game.scenes.game_scene import GameScene
        self._app.scene_manager.replace_with(
            GameScene(self._app),
            FadeTransition(duration=0.4),
        )

    def _on_settings(self) -> None:
        from game.scenes.settings_scene import SettingsScene
        self._app.scene_manager.push_with(
            SettingsScene(self._app),
            SlideTransition(duration=0.3, direction="left"),
        )

    def _on_quit(self) -> None:
        from pygame_engine.ui.feedback.confirm_dialog import ConfirmDialog
        ConfirmDialog.push(
            app=self._app,
            message="Quit the game?",
            confirm_label="Quit",
            cancel_label="Stay",
            on_confirm=self._app.stop,
            danger=False,
        )
