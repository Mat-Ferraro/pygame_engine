"""
game/scenes/pause_scene.py

Pushed on top of GameScene when the player pauses. Renders a
semi-transparent overlay so the game world stays visible behind it.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene, FadeTransition, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack

from game import actions
from game.locale import t


class PauseScene(Scene):
    """Pause menu — resume, settings, or quit to main menu."""

    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = False   # game world stays visible behind

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()

        panel_rect = anchor(screen, (280, 280), "center")
        panel      = Panel(panel_rect)

        title = Label(
            pygame.Rect(panel_rect.x, panel_rect.y - 52, panel_rect.width, 40),
            t("pause.title"),
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        )

        btn_rects = column(
            panel_rect, count=3,
            item_size=(200, 48), spacing=12,
            padding=theme.spacing.xl,
        )
        panel.add(Button(btn_rects[0], t("pause.resume"),   on_click=self._resume))
        panel.add(Button(btn_rects[1], t("pause.settings"), on_click=self._settings))
        panel.add(Button(btn_rects[2], t("pause.quit"),     on_click=self._quit_to_menu))

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.PAUSE) or inp.was_action_pressed(actions.CANCEL):
            self._resume()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        super().render(surface)

    def _resume(self) -> None:
        self._app.scene_manager.pop_with(
            SlideTransition(duration=0.25, direction="up"),
        )

    def _settings(self) -> None:
        from game.scenes.settings_scene import SettingsScene
        self._app.scene_manager.push_with(
            SettingsScene(self._app),
            SlideTransition(duration=0.3, direction="left"),
        )

    def _quit_to_menu(self) -> None:
        from game.scenes.main_menu import MainMenuScene
        self._app.scene_manager.clear_and_push(MainMenuScene(self._app))
