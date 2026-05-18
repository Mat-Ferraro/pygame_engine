"""
Pre-wired with stubs for the most common 2D game systems:
- Camera (follow player, world bounds)
- Tilemap (rendering + collision)
- Lighting (dark overlay with player light)
- Positional audio (listener follows player)
- Animation state machine (idle/run/jump)
- Pathfinding (obstacle grid from tilemap)
- LogPanel for in-game event log
- Pause on ESC or P
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.camera import Camera
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, LogPanel, Stack

from game import actions


class GameScene(Scene):
    """
    Main gameplay scene — replace with your game's content.

    Stub pattern — uncomment the systems you need and fill in
    the game-specific logic.

    Pause key: ESC (CANCEL action) or P (PAUSE action).
    ESC is the standard binding players expect. Both are checked so
    either key opens the pause menu.
    """

    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._camera: Camera | None = None
        self._event_log: LogPanel | None = None

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
            pygame.Rect(12, 12, 300, 22),
            "ESC / P — pause",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
        ))

        # Event log — remove or reposition as needed
        self._event_log = LogPanel(
            rect=pygame.Rect(screen.width - 310, screen.height - 210, 300, 196),
            max_lines=100,
        )
        self._event_log.append("Game started.", colour=(140, 210, 140))
        root.add(self._event_log)

        self.root_widget = root

    def log_event(self, message: str, colour=None) -> None:
        """Append a line to the in-game event log."""
        if self._event_log:
            self._event_log.append(message, colour=colour)

    def on_exit(self) -> None:
        # self._app.audio.stop_music(fade_out_ms=500)
        pass

    def on_pause(self) -> None:
        pass

    def on_resume(self) -> None:
        pass

    def on_resize(self, width: int, height: int) -> None:
        if self._camera:
            self._camera.viewport_size = (width, height)
        self.on_enter()

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        # ESC (CANCEL) and P (PAUSE) both open the pause menu.
        # ESC is the key players expect; P is the explicit pause binding.
        if (inp.was_action_pressed(actions.PAUSE)
                or inp.was_action_pressed(actions.CANCEL)):
            self._open_pause()
            return True
        return False

    def _open_pause(self) -> None:
        from game.scenes.pause_scene import PauseScene
        self._app.scene_manager.push_with(
            PauseScene(self._app),
            SlideTransition(duration=0.25, direction="down"),
        )

    def update(self, dt: float) -> None:
        # When implementing animations that change with time, always check
        # app.reduced_motion first per ACCESSIBILITY_STANDARDS.md Section 4:
#           if not self._app.reduced_motion:
#               self._t += dt

        if self._camera:
            self._camera.update(dt)
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