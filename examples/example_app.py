"""
examples/example_app.py

Minimal end-to-end spine example.

Proves that the full chain works:
    AppConfig -> Application -> SceneManager -> Scene -> Widget

What this example does:
- Opens a window
- Renders a background colour that cycles slowly
- Shows a single coloured rect widget in the centre of the screen
- Displays FPS in the window title
- ESC or closing the window exits cleanly

Run from the repo root:
    python -m examples.example_app
"""

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.scene import Scene
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.ui.base import Widget


# ── A minimal widget ──────────────────────────────────────────────────────────

class ColourBlock(Widget):
    """
    A simple coloured rectangle that pulses its brightness over time.

    Exercises: Widget.__init__, update, render, set_rect, visible/enabled.
    """

    def __init__(self, rect: pygame.Rect, colour: tuple[int, int, int]) -> None:
        super().__init__(rect)
        self._base_colour = colour
        self._t: float = 0.0          # time accumulator for pulse

    def update(self, dt: float) -> None:
        self._t += dt

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        # Pulse brightness between 60% and 100% of the base colour
        pulse = 0.6 + 0.4 * abs(__import__("math").sin(self._t * 2.0))
        colour = tuple(int(c * pulse) for c in self._base_colour)
        pygame.draw.rect(surface, colour, self.rect, border_radius=8)

        # Draw a subtle border
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=8)


# ── A minimal scene ───────────────────────────────────────────────────────────

class ExampleScene(Scene):
    """
    A single scene that owns one ColourBlock widget.

    Exercises: Scene.on_enter, on_exit, on_pause, on_resume,
               handle_event (ESC to quit), update, render,
               root_widget delegation.
    """

    # This scene is fullscreen and blocks everything below it (default).
    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._bg_hue: float = 0.0     # cycles 0..1 for background colour

    def on_enter(self) -> None:
        print("[ExampleScene] on_enter")

        # Build the root widget — a centred colour block.
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
        # Use action query rather than raw key check.
        # CANCEL is bound to K_ESCAPE by default in bindings.py.
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def update(self, dt: float) -> None:
        # Slowly cycle the background hue
        self._bg_hue = (self._bg_hue + dt * 0.05) % 1.0

        # Update title with FPS
        fps = self._app.clock.tick  # clock.tick is the last tick ms value
        pygame.display.set_caption(
            f"{self._app.config.title}  |  "
            f"FPS: {self._app.clock.get_fps():.0f}"
        )

        # Delegate to root widget via super
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        # Draw a slowly shifting dark background
        r, g, b = _hue_to_rgb(self._bg_hue)
        bg = (int(r * 40), int(g * 40), int(b * 40))
        surface.fill(bg)

        # Draw a subtle grid so motion is visible
        _draw_grid(surface, (255, 255, 255), alpha=18)

        # Draw label
        _draw_label(
            surface,
            "pygame_engine  —  spine example",
            (surface.get_width() // 2, 40),
        )
        _draw_label(
            surface,
            "ESC to quit",
            (surface.get_width() // 2, surface.get_height() - 40),
            size=18,
        )

        # Delegate to root widget via super
        super().render(surface)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hue_to_rgb(h: float) -> tuple[float, float, float]:
    """Convert a hue value (0..1) to an RGB triple (each 0..1)."""
    import colorsys
    return colorsys.hsv_to_rgb(h, 0.6, 1.0)


def _draw_grid(
    surface: pygame.Surface,
    colour: tuple[int, int, int],
    alpha: int = 20,
    spacing: int = 60,
) -> None:
    """Draw a faint grid onto the surface using a temporary alpha surface."""
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
    """Render a single line of text centred at the given position."""
    font = pygame.font.SysFont("segoeui,helvetica,arial", size)
    rendered = font.render(text, True, (220, 220, 220))
    rect = rendered.get_rect(center=centre)
    surface.blit(rendered, rect)


# ── Entry point ───────────────────────────────────────────────────────────────

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
