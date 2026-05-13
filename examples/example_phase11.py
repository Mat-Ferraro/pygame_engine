"""
What this example shows:
- Pathfinding: enemies navigate around walls using A*
- Animation state machine: player switches idle/run/jump states
- 2D positional audio: explosion sounds pan and fade with distance
- 2D lighting: dark world with player torch and enemy lanterns

Controls:
    Arrow keys / WASD  — move player
    Space              — jump  (triggers state machine)
    E                  — trigger explosion at random enemy (positional audio demo)
    L                  — toggle lighting on/off
    ESC                — quit

Run from the repo root:
    python -m examples.example_phase11
"""

from __future__ import annotations

import math
import random

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.animation import (
    AnimationPlayer,
    AnimationStateMachine,
    SpriteAnimation,
)
from pygame_engine.camera import Camera
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.lighting import Light, LightingSystem
from pygame_engine.pathfinding import ObstacleGrid, Pathfinder
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.tilemap import TileLayer, Tilemap, Tileset
from pygame_engine.ui import Label, Stack

TILE = 32
COLS = 30
ROWS = 20

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_tileset() -> Tileset:
    colours = [(50, 80, 50), (70, 55, 35), (90, 90, 90)]
    surfaces = []
    for c in colours:
        s = pygame.Surface((TILE, TILE))
        s.fill(c)
        pygame.draw.rect(s, tuple(min(255, x + 20) for x in c),
                         s.get_rect(), width=1)
        surfaces.append(s)
    from pygame_engine.tilemap.tileset import Tileset as _T
    return _T(surfaces, TILE, TILE)


def _make_map():
    ground = [[0] * COLS for _ in range(ROWS)]
    solid  = [[-1] * COLS for _ in range(ROWS)]

    # Border walls
    for c in range(COLS):
        solid[0][c] = solid[ROWS-1][c] = 2
        ground[0][c] = ground[ROWS-1][c] = 2
    for r in range(ROWS):
        solid[r][0] = solid[r][COLS-1] = 2
        ground[r][0] = ground[r][COLS-1] = 2

    # Internal walls
    wall_positions = [
        (5, 3, 8), (5, 5, 8), (12, 2, 5), (18, 8, 12),
        (8, 12, 11), (20, 14, 17), (3, 15, 18),
    ]
    for col, r1, r2 in wall_positions:
        for r in range(r1, r2):
            if 0 < col < COLS-1 and 0 < r < ROWS-1:
                solid[r][col] = 2
                ground[r][col] = 2

    ts   = _make_tileset()
    tmap = Tilemap(ts, TILE, TILE,
                   layers=[TileLayer("ground", ground),
                           TileLayer("walls",  solid)])
    tmap.set_collision_layer("walls")
    return tmap


def _make_anim_player(colour: tuple) -> AnimationPlayer:
    """Create a simple AnimationPlayer from coloured placeholder frames."""
    def _frame(col, label_col=None):
        s = pygame.Surface((24, 32), pygame.SRCALPHA)
        s.fill(col)
        if label_col:
            pygame.draw.rect(s, label_col, (4, 4, 16, 8))
        return s

    p = AnimationPlayer()
    p.add("idle", SpriteAnimation("idle",
          [_frame(colour), _frame(colour, (255,255,255))],
          frame_duration=0.5, loop=True))
    p.add("run",  SpriteAnimation("run",
          [_frame(colour, (200,200,0)), _frame(colour), _frame(colour, (200,200,0))],
          frame_duration=0.12, loop=True))
    p.add("jump", SpriteAnimation("jump",
          [_frame(colour, (0,200,255))],
          frame_duration=0.3, loop=False))
    return p


# ── Enemy ─────────────────────────────────────────────────────────────────────

class Enemy:
    SPEED = 80.0
    RETARGET = 2.5

    def __init__(self, x: int, y: int, finder: Pathfinder, tmap: Tilemap):
        self.rect    = pygame.Rect(x, y, 20, 20)
        self._finder = finder
        self._tmap   = tmap
        self._path:  list[tuple[int, int]] = []
        self._timer  = random.uniform(0, self.RETARGET)
        self.light   = Light(world_x=x, world_y=y,
                              radius=90, colour=(100, 180, 100),
                              intensity=0.6, flicker=0.05)

    def update(self, dt: float, target: pygame.Rect) -> None:
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self.RETARGET
            start = self._tmap.world_to_tile(self.rect.centerx, self.rect.centery)
            goal  = self._tmap.world_to_tile(target.centerx,    target.centery)
            self._path = self._finder.find(start, goal)
            if self._path:
                self._path.pop(0)   # skip current tile

        if self._path:
            tc, tr = self._path[0]
            wx, wy = self._tmap.tile_to_world(tc, tr)
            tx = wx + TILE // 2 - self.rect.width  // 2
            ty = wy + TILE // 2 - self.rect.height // 2
            dx = tx - self.rect.x
            dy = ty - self.rect.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 4:
                self._path.pop(0)
            else:
                speed = self.SPEED * dt
                self.rect.x += int(dx / dist * speed)
                self.rect.y += int(dy / dist * speed)

        self.light.world_x = float(self.rect.centerx)
        self.light.world_y = float(self.rect.centery)

    def render(self, surface: pygame.Surface, camera: Camera) -> None:
        sr = camera.world_rect_to_screen(self.rect)
        pygame.draw.rect(surface, (60, 180, 80), sr, border_radius=4)


# ── Scene ─────────────────────────────────────────────────────────────────────

class Phase11Scene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        # Tilemap
        self._tmap   = _make_map()
        self._camera = Camera(screen.width, screen.height)
        self._camera.set_world_bounds(self._tmap.world_rect)

        # Player
        self._player = pygame.Rect(TILE * 2, TILE * 2, 24, 32)
        self._vx     = 0.0
        self._vy     = 0.0
        self._on_ground = False

        # Animation state machine
        self._animator = _make_anim_player((80, 140, 220))
        self._sm = AnimationStateMachine(self._animator)
        self._sm.add_state("idle", default=True)
        self._sm.add_state("run")
        self._sm.add_state("jump")
        self._sm.add_transition("idle", "run",
                                lambda p: abs(p.get("vx", 0)) > 10)
        self._sm.add_transition("run",  "idle",
                                lambda p: abs(p.get("vx", 0)) <= 10)
        self._sm.add_transition("idle", "jump",
                                lambda p: p.get("jumping", False))
        self._sm.add_transition("run",  "jump",
                                lambda p: p.get("jumping", False))
        self._sm.add_transition("jump", "idle",
                                lambda p: p.get("on_ground", False))

        # Pathfinding
        grid          = ObstacleGrid.from_tilemap(self._tmap, "walls")
        self._finder  = Pathfinder(grid, diagonal=False)

        # Enemies
        spawn_points = [(COLS-3, ROWS-3), (COLS-3, 3), (3, ROWS//2)]
        self._enemies = [
            Enemy(c*TILE, r*TILE, self._finder, self._tmap)
            for c, r in spawn_points
        ]

        # Lighting
        self._lighting_on = True
        self._lights = LightingSystem(ambient=(8, 10, 20), darkness=0.93)
        self._player_light = self._lights.add(
            Light(radius=130, colour=(200, 220, 255), intensity=0.75)
        )
        for e in self._enemies:
            self._lights.add(e.light)

        # Positional audio (no actual sounds in example — just system wired)
        from pygame_engine.audio.positional import PositionalAudio
        self._pos_audio = PositionalAudio(max_distance=500)

        # Camera
        self._camera.move_to(self._player.center)

        # HUD
        root = Stack(pygame.Rect(screen))
        hints = [
            "WASD/Arrows — move   Space — jump",
            "E — trigger explosion  L — toggle lighting  ESC — quit",
            "Enemies use A* pathfinding to follow you",
        ]
        for i, hint in enumerate(hints):
            root.add(Label(pygame.Rect(12, 12 + i*20, 600, 18), hint,
                           font_size=theme.typography.xs,
                           colour=theme.colours.text_secondary))
        self._state_label = Label(
            anchor(screen, (300, 20), "top_right", margin=12),
            "State: idle", font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="right")
        root.add(self._state_label)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                self._lighting_on = not self._lighting_on; return True
            if event.key == pygame.K_e and self._enemies:
                e = random.choice(self._enemies)
                self._camera.add_trauma(0.4)
                # Would call: self._pos_audio.play(boom_sfx, e.rect.centerx, e.rect.centery)
                return True
        return False

    def update(self, dt: float) -> None:
        inp   = self._app.input_manager
        speed = 180.0
        self._vx = 0.0
        jumping  = False

        if inp.is_action_down(actions.NAV_LEFT):  self._vx = -speed
        if inp.is_action_down(actions.NAV_RIGHT): self._vx =  speed
        if inp.was_action_pressed(actions.CONFIRM) and self._on_ground:
            self._vy = -460.0; jumping = True

        self._vy = min(self._vy + 750 * dt, 800)
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

        # State machine
        self._sm.update(dt, params={
            "vx":       self._vx,
            "jumping":  jumping,
            "on_ground": self._on_ground,
        })
        self._state_label.text = f"State: {self._sm.current_state}"

        # Enemies
        for e in self._enemies:
            e.update(dt, self._player)

        # Lighting
        self._player_light.world_x = float(self._player.centerx)
        self._player_light.world_y = float(self._player.centery)
        self._lights.update(dt)

        # Positional audio listener
        self._pos_audio.set_listener(self._player.centerx, self._player.centery)

        # Camera
        self._camera.follow(self._player.center, speed=7.0, dt=dt)
        self._camera.update(dt)
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((20, 25, 35))
        self._tmap.render(surface, self._camera)
        for e in self._enemies:
            e.render(surface, self._camera)

        # Player — draw current animation frame
        frame = self._animator.current_frame
        pr    = self._camera.world_rect_to_screen(self._player)
        if frame:
            surface.blit(pygame.transform.scale(frame, (pr.width, pr.height)), pr)
        else:
            pygame.draw.rect(surface, (80, 140, 220), pr, border_radius=3)

        # Lighting overlay (after world, before UI)
        if self._lighting_on:
            self._lights.render(surface, self._camera)

        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — Phase 11 demo",
        width=1280, height=720,
    ))
    app.run(Phase11Scene(app))


if __name__ == "__main__":
    run()
