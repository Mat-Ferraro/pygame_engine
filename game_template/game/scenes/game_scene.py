"""
game/scenes/game_scene.py

Main gameplay scene. Replace placeholder content with your game logic.

Pre-wired with stubs for the most common 2D game systems:
- Camera (follow player, world bounds)
- Tilemap (rendering + collision)
- Lighting (dark overlay with player light)
- Positional audio (listener follows player)
- Animation state machine (idle/run/jump)
- Pathfinding (obstacle grid from tilemap)
- Pause on ESC
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.camera import Camera
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Stack

from game import actions


class GameScene(Scene):
    """
    Main gameplay scene — replace with your game's content.

    Stub pattern — uncomment the systems you need and fill in
    the game-specific logic.
    """

    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._camera: Camera | None = None

        # ── Uncomment the systems you need ────────────────────────────────────
        # from pygame_engine.lighting import LightingSystem, Light
        # from pygame_engine.audio.positional import PositionalAudio
        # from pygame_engine.pathfinding import ObstacleGrid, Pathfinder
        # from pygame_engine.animation import AnimationStateMachine

        # self._lights:    LightingSystem | None = None
        # self._pos_audio: PositionalAudio | None = None
        # self._finder:    Pathfinder | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect

        # ── Camera ────────────────────────────────────────────────────────────
        self._camera = Camera(screen.width, screen.height)
        # self._camera.set_world_bounds(self._tmap.world_rect)
        # self._camera.move_to(player_start_pos)

        # ── Tilemap ───────────────────────────────────────────────────────────
        # from pygame_engine.tilemap import Tilemap, Tileset, TileLayer
        # from pathlib import Path
        # tileset      = Tileset.from_file(
        #     self._app.assets.asset_root / "images" / "tiles.png", 16, 16
        # )
        # ground_layer = TileLayer("ground", your_grid_data)
        # wall_layer   = TileLayer("walls",  your_wall_data)
        # self._tmap   = Tilemap(tileset, 16, 16, layers=[ground_layer, wall_layer])
        # self._tmap.set_collision_layer("walls")

        # ── Lighting ──────────────────────────────────────────────────────────
        # from pygame_engine.lighting import LightingSystem, Light
        # self._lights = LightingSystem(ambient=(10, 15, 30), darkness=0.9)
        # self._player_light = self._lights.add(
        #     Light(radius=130, colour=(200, 220, 255), intensity=0.75)
        # )

        # ── Positional audio ──────────────────────────────────────────────────
        # from pygame_engine.audio.positional import PositionalAudio
        # self._pos_audio = PositionalAudio(max_distance=600)

        # ── Pathfinding ───────────────────────────────────────────────────────
        # from pygame_engine.pathfinding import ObstacleGrid, Pathfinder
        # grid         = ObstacleGrid.from_tilemap(self._tmap, "walls")
        # self._finder = Pathfinder(grid, diagonal=True)

        # ── Animation state machine ───────────────────────────────────────────
        # from pygame_engine.animation import AnimationStateMachine
        # self._sm = AnimationStateMachine(self._player.animator)
        # self._sm.add_state("idle", default=True)
        # self._sm.add_state("run")
        # self._sm.add_state("jump")
        # self._sm.add_transition("idle", "run",  lambda p: abs(p["vx"]) > 10)
        # self._sm.add_transition("run",  "idle", lambda p: abs(p["vx"]) <= 10)
        # self._sm.add_transition("*",    "dead", lambda p: p["hp"] <= 0, priority=10)

        # ── Music ─────────────────────────────────────────────────────────────
        # self._app.audio.play_music(
        #     self._app.assets.asset_root / "sounds" / "music_game.ogg"
        # )

        # ── HUD ───────────────────────────────────────────────────────────────
        theme = get_theme()
        root  = Stack(pygame.Rect(screen))
        root.add(Label(
            pygame.Rect(12, 12, 400, 22),
            "ESC — pause",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
        ))
        self.root_widget = root

    def on_exit(self) -> None:
        # self._app.audio.stop_music(fade_out_ms=500)
        pass

    def on_pause(self) -> None:
        pass   # stop timers, animations if needed

    def on_resume(self) -> None:
        pass   # resume timers, refresh input state

    def on_resize(self, width: int, height: int) -> None:
        if self._camera:
            self._camera.viewport_size = (width, height)
        self.on_enter()   # rebuild HUD at new size

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.PAUSE):
            from game.scenes.pause_scene import PauseScene
            self._app.scene_manager.push_with(
                PauseScene(self._app),
                SlideTransition(duration=0.25, direction="down"),
            )
            return True
        return False

    def update(self, dt: float) -> None:
        # ── Update player ─────────────────────────────────────────────────────
        # self._player.update(dt)

        # ── Update state machine ──────────────────────────────────────────────
        # self._sm.update(dt, params={"vx": player.vx, "hp": player.hp})

        # ── Update camera ─────────────────────────────────────────────────────
        if self._camera:
            # self._camera.follow(self._player.rect.center, speed=6, dt=dt)
            self._camera.update(dt)

        # ── Update lighting ───────────────────────────────────────────────────
        # if self._lights:
        #     self._player_light.world_x = self._player.rect.centerx
        #     self._player_light.world_y = self._player.rect.centery
        #     self._lights.update(dt)

        # ── Update positional audio ───────────────────────────────────────────
        # if self._pos_audio:
        #     self._pos_audio.set_listener(*self._player.rect.center)

        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_dark)

        # ── Render tilemap ────────────────────────────────────────────────────
        # self._tmap.render(surface, self._camera)

        # ── Render entities ───────────────────────────────────────────────────
        # for entity in self._entities:
        #     if self._camera.is_visible(entity.rect, margin=32):
        #         screen_rect = self._camera.world_rect_to_screen(entity.rect)
        #         surface.blit(entity.image, screen_rect)

        # ── Lighting overlay (after world, before UI) ─────────────────────────
        # if self._lights:
        #     self._lights.render(surface, self._camera)

        super().render(surface)   # HUD on top
