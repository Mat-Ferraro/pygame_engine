"""Main menu — Start, Settings, Quit with ConfirmDialog on quit."""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene, FadeTransition, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack

from game import actions
from game.locale import t


class MainMenuScene(Scene):
    """
    Main menu — Start, Settings, Quit.

    Demonstrates:
    - Panel + column layout for button groups
    - Localisation via t() for all user-visible strings
    - Scene transitions on navigation
    - ConfirmDialog on quit
    """

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()

        title = Label(
            anchor(screen, (500, 60), "top", margin=80),
            self._app.config.title,
            font_size=theme.typography.xxl,
            colour=theme.colours.text,
            align="center",
        )

        panel_rect = anchor(screen, (280, 240), "center", offset=(0, 30))
        panel      = Panel(panel_rect)

        btn_rects = column(
            panel_rect, count=3,
            item_size=(200, 52), spacing=14,
            padding=theme.spacing.xl,
        )
        panel.add(Button(btn_rects[0], t("menu.start"),    on_click=self._on_start))
        panel.add(Button(btn_rects[1], t("menu.settings"), on_click=self._on_settings))
        panel.add(Button(btn_rects[2], t("menu.quit"),     on_click=self._on_quit))

        version = Label(
            anchor(screen, (200, 24), "bottom_right", margin=12),
            "v1.3.0",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            align="right",
        )

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        root.add(version)
        self.root_widget = root

    def on_exit(self) -> None:
        pass

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

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)

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
