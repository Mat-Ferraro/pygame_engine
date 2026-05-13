"""
game/scenes/settings_scene.py

Settings scene.

Pushed on top of the main menu (or game scene). Slides in, pops back
on Back or ESC.

Extend this with actual settings controls:
- Volume sliders (use ProgressBar + InputManager)
- Fullscreen toggle (Button that calls AppConfig)
- Keybinding display
- Resolution selection (Dropdown)
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.scene.transitions import SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack

from game import actions


class SettingsScene(Scene):
    """Settings overlay — pushed on top, pops back on ESC or Back."""

    # Does not block rendering below — scene beneath stays visible
    blocks_input_below  = True
    blocks_update_below = False
    blocks_render_below = False

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        theme  = get_theme()

        # ── Settings panel ────────────────────────────────────────────────────
        panel_rect = anchor(screen, (360, 320), "center")
        panel = Panel(panel_rect)

        # Title
        title_rect = pygame.Rect(panel_rect.x, panel_rect.y - 52,
                                 panel_rect.width, 40)
        title = Label(title_rect, "Settings",
                      font_size=theme.typography.xl,
                      colour=theme.colours.text,
                      align="center")

        btn_rects = column(
            panel_rect, count=1,
            item_size=(220, 48), spacing=0,
            padding=theme.spacing.xl,
        )

        # Placeholder — add real settings controls here
        btn_back = Button(btn_rects[0], "Back",
                          on_click=self._go_back)

        panel.add(btn_back)

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._go_back()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay over the scene below
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))
        super().render(surface)

    def _go_back(self) -> None:
        self._app.scene_manager.pop_with(
            SlideTransition(duration=0.3, direction="right"),
        )
