"""
examples/example_app.py

Minimal end-to-end spine example.

Proves that the full chain works and demonstrates core systems:
    AppConfig → Application → SceneManager → Scene → Widget
    + InputManager (action queries)
    + Layout (anchor)
    + Theme (colours, typography)
    + Tween + easing (animated widget)
    + Timer (FPS display)

What you see:
- Dark background that slowly shifts colour
- A centred widget that pulses and slides in on entry
- FPS counter in the window title
- ESC exits via the action system

Run from the repo root:
    python -m examples.example_app
"""

import math

import pygame

from pygame_engine.animation import Tween
from pygame_engine.animation.easing import ease_out_back
from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label
from pygame_engine.ui.base.widget import Widget


# ── Animated widget ───────────────────────────────────────────────────────────

class AnimatedBlock(Widget):
    """
    A coloured rectangle that:
    - slides in from below on creation (Tween + ease_out_back)
    - pulses its brightness continuously (sine wave)
    - draws a centred label
    """

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        theme = get_theme()

        self._t:     float = 0.0
        self._start_y = rect.y + 120   # start below final position

        # Slide-in tween
        self._slide = Tween(
            start=self._start_y,
            end=rect.y,
            duration=0.6,
            easing=ease_out_back,
            auto_start=True,
        )

        self._label = Label(
            pygame.Rect(rect),
            "pygame_engine",
            font_size=theme.typography.lg,
            colour=theme.colours.text,
            align="center",
        )

    def update(self, dt: float) -> None:
        self._t += dt
        self._slide.update(dt)
        self.rect.y = int(self._slide.value)
        self._label.set_rect(pygame.Rect(self.rect))

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        theme  = get_theme()
        pulse  = 0.65 + 0.35 * abs(math.sin(self._t * 1.8))
        colour = tuple(int(c * pulse) for c in theme.colours.bg_overlay)

        pygame.draw.rect(surface, colour, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme.colours.border, self.rect,
                         width=1, border_radius=10)
        self._label.render(surface)


# ── Scene ─────────────────────────────────────────────────────────────────────

class ExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._hue: float = 0.0

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        self.root_widget = AnimatedBlock(
            anchor(screen, (340, 100), "center")
        )

    def on_exit(self) -> None:
        print("[ExampleScene] on_exit")

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def update(self, dt: float) -> None:
        self._hue = (self._hue + dt * 0.04) % 1.0
        pygame.display.set_caption(
            f"{self._app.config.title}  —  "
            f"{self._app.clock.get_fps():.0f} fps"
        )
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(self._hue, 0.4, 0.14)
        surface.fill((int(r * 255), int(g * 255), int(b * 255)))

        theme = get_theme()
        font  = pygame.font.SysFont(theme.typography.family,
                                    theme.typography.xs)
        hint  = font.render("ESC to quit", True, theme.colours.text_secondary)
        surface.blit(hint, (
            surface.get_width()  // 2 - hint.get_width()  // 2,
            surface.get_height() - 32,
        ))

        super().render(surface)


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    config = AppConfig(
        title="pygame_engine — spine example",
        width=1280,
        height=720,
        target_fps=60,
    )
    app = Application(config)
    app.run(ExampleScene(app))


if __name__ == "__main__":
    run()
