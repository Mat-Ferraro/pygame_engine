"""
game/scenes/game_scene.py

Main gameplay scene.

This is where your game actually happens. Replace the placeholder content
with your real gameplay logic, systems, and entities.

The scene is pre-wired with:
- Pause on ESC (pushes PauseScene)
- Debug overlay toggle on F1 (engine built-in)
- dt-based update loop
- Blank render with theme background
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.scene import Scene
from pygame_engine.scene.transitions import SlideTransition
from pygame_engine.theme.runtime import get_theme

from game import actions


class GameScene(Scene):
    """
    Main gameplay scene — replace with your game's content.

    Suggested additions:
    - Load assets in on_enter via self._app.assets
    - Initialise your game systems (physics, AI, etc.)
    - Build a HUD using engine widgets
    - Play music via self._app.audio
    - Save/load via SaveManager
    """

    # This is a full-screen scene that blocks everything below it
    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        """Initialise game state, load assets, build HUD."""
        # Example:
        # self._player = Player(start_pos=(640, 360))
        # self._app.audio.play_music(
        #     self._app.assets.asset_root / "sounds" / "music_game.ogg"
        # )
        pass

    def on_exit(self) -> None:
        """Clean up — stop music, save state if needed."""
        # self._app.audio.stop_music(fade_out_ms=500)
        pass

    def on_pause(self) -> None:
        """Called when a scene is pushed on top (e.g. pause menu)."""
        pass

    def on_resume(self) -> None:
        """Called when returning from a pushed scene."""
        pass

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager

        # Pause menu
        if inp.was_action_pressed(actions.PAUSE):
            from game.scenes.pause_scene import PauseScene
            self._app.scene_manager.push_with(
                PauseScene(self._app),
                SlideTransition(duration=0.25, direction="down"),
            )
            return True

        return False

    def update(self, dt: float) -> None:
        """Update all game systems each frame."""
        # self._player.update(dt)
        # self._world.update(dt)
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """Render the game world and HUD."""
        surface.fill(get_theme().colours.bg_dark)

        # self._world.render(surface)
        # self._player.render(surface)

        super().render(surface)   # renders HUD (root_widget if set)
