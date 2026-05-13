"""
Demonstrates the Tilemap system with Camera integration.

What this example shows:
- Building a tilemap from code (no file needed)
- Multi-layer rendering (ground + decoration)
- Collision detection and simple resolution
- Camera following the player with world bounds

Controls:
    Arrow keys / WASD — move player
    Space             — jump
    ESC               — quit

Run from the repo root:
    python -m examples.example_tilemap
"""

from __future__ import annotations
import pygame
from pygame_engine.app import Application, AppConfig
from pygame_engine.camera import Camera
from pygame_engine.input import actions
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.tilemap import TileLayer, Tilemap, Tileset
from pygame_engine.ui import Label, Stack

TILE  = 32
COLS  = 40
ROWS  = 20
GRAVITY = 800


def _build_tileset() -> Tileset:
    """Build a simple colour-based tileset (no image file needed)."""
    colours = [
        (60, 100, 60),   # 0 grass
        (80, 60, 40),    # 1 dirt
        (120, 120, 120), # 2 stone
        (200, 180, 80),  # 3 sand
        (40, 80, 160),   # 4 water
    ]
    surfaces = []
    for col in colours:
        s = pygame.Surface((TILE, TILE))
        s.fill(col)
        pygame.draw.rect(s, tuple(min(255, c + 30) for c in col),
                         s.get_rect(), width=1)
        surfaces.append(s)
    from pygame_engine.tilemap.tileset import Tileset as _T
    return _T(surfaces, TILE, TILE)


def _build_map() -> Tilemap:
    ground = [[-1] * COLS for _ in range(ROWS)]
    solid  = [[-1] * COLS for _ in range(ROWS)]

    # Floor
    for c in range(COLS):
        ground[ROWS-1][c] = 1
        solid[ROWS-1][c]  = 1
        ground[ROWS-2][c] = 0
        solid[ROWS-2][c]  = 1

    # Platforms
    for c in range(5, 12):
        ground[14][c] = 0; solid[14][c] = 1
    for c in range(16, 24):
        ground[11][c] = 0; solid[11][c] = 1
    for c in range(28, 36):
        ground[13][c] = 2; solid[13][c] = 1

    # Walls
    for r in range(ROWS - 5, ROWS - 1):
        ground[r][20] = 2; solid[r][20] = 1

    ts   = _build_tileset()
    gl   = TileLayer("ground", ground)
    sl   = TileLayer("collision", solid)
    tmap = Tilemap(ts, TILE, TILE, layers=[gl, sl])
    tmap.set_collision_layer("collision")
    return tmap


class TilemapExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._tmap   = _build_map()
        self._player = pygame.Rect(96, (ROWS - 4) * TILE, 24, 32)
        self._vx     = 0.0
        self._vy     = 0.0
        self._on_ground = False
        self._camera: Camera | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()
        self._camera = Camera(screen.width, screen.height)
        self._camera.set_world_bounds(self._tmap.world_rect)
        self._camera.move_to(self._player.center)

        root = Stack(pygame.Rect(screen))
        root.add(Label(pygame.Rect(12, 12, 500, 20),
                       "Arrows/WASD — move   Space — jump   ESC — quit",
                       font_size=theme.typography.xs,
                       colour=theme.colours.text_secondary))
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        from pygame_engine.input import actions as a
        if self._app.input_manager.was_action_pressed(a.CANCEL):
            self._app.stop(); return True
        return False

    def update(self, dt: float) -> None:
        inp = self._app.input_manager
        speed = 180.0
        self._vx = 0.0
        if inp.is_action_down(actions.NAV_LEFT):  self._vx = -speed
        if inp.is_action_down(actions.NAV_RIGHT): self._vx =  speed
        if inp.was_action_pressed(actions.CONFIRM) and self._on_ground:
            self._vy = -480.0

        self._vy = min(self._vy + GRAVITY * dt, 900)
        self._player.x += int(self._vx * dt)
        for t in self._tmap.get_colliding_tiles(self._player):
            if self._vx > 0: self._player.right = t.left
            elif self._vx < 0: self._player.left = t.right
            self._vx = 0

        self._on_ground = False
        self._player.y += int(self._vy * dt)
        for t in self._tmap.get_colliding_tiles(self._player):
            if self._vy > 0:
                self._player.bottom = t.top; self._on_ground = True
            elif self._vy < 0:
                self._player.top = t.bottom
            self._vy = 0

        if self._camera:
            self._camera.follow(self._player.center, speed=7.0, dt=dt)
            self._camera.update(dt)
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((30, 40, 55))
        if self._camera:
            self._tmap.render(surface, self._camera)
            pr = self._camera.world_rect_to_screen(self._player)
            pygame.draw.rect(surface, (80, 160, 220), pr, border_radius=3)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(title="pygame_engine — tilemap", width=1280, height=720))
    app.run(TilemapExampleScene(app))

if __name__ == "__main__":
    run()
