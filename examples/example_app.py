"""
examples/example_app.py

Minimal end-to-end spine example.
"""

import colorsys
import math
import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene
from pygame_engine.ui.base import Widget


class ColourBlock(Widget):
    def __init__(self, rect: pygame.Rect, colour: tuple[int, int, int]) -> None:
        super().__init__(rect)
        self._base_colour = colour
        self._t: float = 0.0

    def update(self, dt: float) -> None:
        self._t += dt

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pulse = 0.6 + 0.4 * abs(math.sin(self._t * 2.0))
        colour = tuple(int(c * pulse) for c in self._base_colour)
        pygame.draw.rect(surface, colour, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=8)


class ExampleScene(Scene):
    blocks_input_below = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._bg_hue: float = 0.0

    def on_enter(self) -> None:
        print("[ExampleScene] on_enter")
        screen = pygame.Rect(0, 0, self._app.config.width, self._app.config.height)
        rect = anchor(screen, (200, 120), "center")
        self.root_widget = ColourBlock(rect, (100, 160, 240))

    def on_exit(self) -> None:
        print("[ExampleScene] on_exit")

    def on_pause(self) -> None:
        print("[ExampleScene] on_pause")

    def on_resume(self) -> None:
        print("[ExampleScene] on_resume")

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def update(self, dt: float) -> None:
        self._bg_hue = (self._bg_hue + dt * 0.05) % 1.0
        pygame.display.set_caption(
            f"{self._app.config.title}  |  "
            f"FPS: {self._app.clock.get_fps():.0f}"
        )
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        r, g, b = colorsys.hsv_to_rgb(self._bg_hue, 0.6, 1.0)
        bg = (int(r * 40), int(g * 40), int(b * 40))
        surface.fill(bg)
        _draw_grid(surface, (255, 255, 255), alpha=18)
        _draw_label(surface, "pygame_engine  —  spine example", (surface.get_width() // 2, 40))
        _draw_label(surface, "ESC to quit", (surface.get_width() // 2, surface.get_height() - 40), size=18)
        super().render(surface)


def _draw_grid(
    surface: pygame.Surface,
    colour: tuple[int, int, int],
    alpha: int = 20,
    spacing: int = 60,
) -> None:
    w, h = surface.get_size()
    grid_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    line_colour = (*colour, alpha)
    for x in range(0, w, spacing):
        pygame.draw.line(grid_surf, line_colour, (x, 0), (x, h))
    for y in range(0, h, spacing):
        pygame.draw.line(grid_surf, line_colour, (0, y), (w, y))
    surface.blit(grid_surf, (0, 0))


def _draw_label(
    surface: pygame.Surface,
    text: str,
    centre: tuple[int, int],
    size: int = 22,
) -> None:
    font = pygame.font.SysFont("segoeui,helvetica,arial", size)
    rendered = font.render(text, True, (220, 220, 220))
    rect = rendered.get_rect(center=centre)
    surface.blit(rendered, rect)


def run() -> None:
    config = AppConfig(
        title="pygame_engine — spine example",
        width=1280,
        height=720,
        target_fps=60,
        debug=False,
    )
    app = Application(config)
    app.run(ExampleScene(app))


if __name__ == "__main__":
    run()
