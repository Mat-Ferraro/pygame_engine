"""
Demonstrates the Camera system.

What this example shows:
- Camera smooth follow on a moving target
- World-to-screen coordinate conversion for rendering world entities
- Screen shake triggered by spacebar
- Camera world bounds clamping
- Zoom in/out with +/- keys

Controls:
    Arrow keys / WASD — move the player
    Space             — trigger screen shake
    + / -             — zoom in / out
    R                 — reset camera
    ESC               — quit

Run from the repo root:
    python -m examples.example_camera
"""

from __future__ import annotations
import pygame
from pygame_engine.app import Application, AppConfig
from pygame_engine.camera import Camera
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Stack

WORLD_W, WORLD_H = 3200, 2400
PLAYER_SPEED     = 220


class CameraExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._camera: Camera | None = None
        self._player = pygame.Rect(WORLD_W // 2, WORLD_H // 2, 32, 32)

        # Scatter some "world objects"
        import random
        rng = random.Random(42)
        self._coins = [
            pygame.Rect(rng.randint(64, WORLD_W - 64),
                        rng.randint(64, WORLD_H - 64), 16, 16)
            for _ in range(60)
        ]

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        self._camera = Camera(screen.width, screen.height)
        self._camera.set_world_bounds(pygame.Rect(0, 0, WORLD_W, WORLD_H))
        self._camera.move_to(self._player.center)

        hints = [
            "Arrows/WASD — move   Space — shake",
            "+/- — zoom   R — reset   ESC — quit",
        ]
        root = Stack(pygame.Rect(screen))
        for i, hint in enumerate(hints):
            root.add(Label(pygame.Rect(12, 12 + i * 22, 500, 20), hint,
                           font_size=theme.typography.xs,
                           colour=theme.colours.text_secondary))
        self._info = Label(anchor(screen, (320, 22), "top_right", margin=12),
                           "", font_size=theme.typography.xs,
                           colour=theme.colours.text_secondary, align="right")
        root.add(self._info)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self._camera:
                self._camera.add_trauma(0.7); return True
            if event.key in (pygame.K_PLUS, pygame.K_EQUALS) and self._camera:
                self._camera.zoom = min(4.0, self._camera.zoom + 0.1); return True
            if event.key == pygame.K_MINUS and self._camera:
                self._camera.zoom = max(0.25, self._camera.zoom - 0.1); return True
            if event.key == pygame.K_r and self._camera:
                self._camera.zoom = 1.0
                self._camera.move_to(self._player.center); return True
        return False

    def update(self, dt: float) -> None:
        inp   = self._app.input_manager
        speed = PLAYER_SPEED * dt
        if inp.is_action_down(actions.NAV_LEFT):  self._player.x -= int(speed)
        if inp.is_action_down(actions.NAV_RIGHT): self._player.x += int(speed)
        if inp.is_action_down(actions.NAV_UP):    self._player.y -= int(speed)
        if inp.is_action_down(actions.NAV_DOWN):  self._player.y += int(speed)
        self._player.clamp_ip(pygame.Rect(0, 0, WORLD_W, WORLD_H))

        if self._camera:
            self._camera.follow(self._player.center, speed=6.0, dt=dt)
            self._camera.update(dt)
            cx, cy = self._camera.position
            self._info.text = (
                f"World: ({self._player.centerx}, {self._player.centery})  "
                f"Zoom: {self._camera.zoom:.2f}  "
                f"Trauma: {self._camera.trauma:.2f}"
            )
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((18, 24, 18))
        if not self._camera:
            super().render(surface); return

        # World boundary
        br = self._camera.world_rect_to_screen(pygame.Rect(0, 0, WORLD_W, WORLD_H))
        pygame.draw.rect(surface, (40, 60, 40), br, width=2)

        # Grid lines every 200px
        for gx in range(0, WORLD_W, 200):
            sx, sy = self._camera.world_to_screen((gx, 0))
            ex, ey = self._camera.world_to_screen((gx, WORLD_H))
            pygame.draw.line(surface, (30, 45, 30), (sx, sy), (ex, ey))
        for gy in range(0, WORLD_H, 200):
            sx, sy = self._camera.world_to_screen((0, gy))
            ex, ey = self._camera.world_to_screen((WORLD_W, gy))
            pygame.draw.line(surface, (30, 45, 30), (sx, sy), (ex, ey))

        # Coins (cull off-screen)
        for coin in self._coins:
            if self._camera.is_visible(coin, margin=16):
                sr = self._camera.world_rect_to_screen(coin)
                pygame.draw.ellipse(surface, (210, 170, 40), sr)

        # Player
        pr = self._camera.world_rect_to_screen(self._player)
        pygame.draw.rect(surface, (80, 140, 220), pr, border_radius=4)
        pygame.draw.rect(surface, (160, 200, 255), pr, width=2, border_radius=4)

        super().render(surface)


def run() -> None:
    app = Application(AppConfig(title="pygame_engine — camera", width=1280, height=720))
    app.run(CameraExampleScene(app))

if __name__ == "__main__":
    run()
