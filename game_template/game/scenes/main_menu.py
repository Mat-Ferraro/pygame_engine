"""
game/scenes/main_menu.py

Main menu scene.

The first scene the player sees. Provides Start, Settings, and Quit.
Replace placeholder callbacks with real scene transitions as your game
grows.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.scene.transitions import FadeTransition, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack

from game import actions


class MainMenuScene(Scene):
    """
    Main menu — Start, Settings, Quit.

    Demonstrates:
    - Panel + column layout for button groups
    - Stack as a transparent root container
    - Scene transitions on navigation
    - Action-based ESC handling
    """

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        theme  = get_theme()

        # ── Title ─────────────────────────────────────────────────────────────
        title_rect = anchor(screen, (500, 60), "top", margin=80)
        title = Label(
            title_rect,
            self._app.config.title,
            font_size=theme.typography.xxl,
            colour=theme.colours.text,
            align="center",
        )

        # ── Button panel ──────────────────────────────────────────────────────
        panel_rect = anchor(screen, (280, 240), "center", offset=(0, 30))
        panel = Panel(panel_rect)

        btn_rects = column(
            panel_rect, count=3,
            item_size=(200, 52), spacing=14,
            padding=theme.spacing.xl,
        )

        btn_start    = Button(btn_rects[0], "Start Game",
                              on_click=self._on_start)
        btn_settings = Button(btn_rects[1], "Settings",
                              on_click=self._on_settings)
        btn_quit     = Button(btn_rects[2], "Quit",
                              on_click=self._app.stop)

        panel.add(btn_start)
        panel.add(btn_settings)
        panel.add(btn_quit)

        # ── Version label ─────────────────────────────────────────────────────
        version_rect = anchor(screen, (200, 24), "bottom_right", margin=12)
        version = Label(
            version_rect, "v0.1.0",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            align="right",
        )

        # ── Root ──────────────────────────────────────────────────────────────
        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        root.add(version)
        self.root_widget = root

    def on_exit(self) -> None:
        pass

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        # ESC on the main menu quits (or you could open a confirm dialog)
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
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
