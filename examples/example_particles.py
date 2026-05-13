"""
examples/example_particles.py

Demonstrates the pygame_engine particle system.

What this example shows:
- All six particle presets: explosion, sparkle, smoke, fire, trail, hit_effect
- Click anywhere to trigger an explosion + sparkle burst at that position
- Right-click for a hit effect
- Continuous fire emitter follows the mouse
- Continuous smoke emitter in the bottom-left corner
- F key toggles fast rendering (no alpha) vs quality rendering (with alpha)
- FPS counter in the window title

Controls:
    Left click  — explosion + sparkle at cursor
    Right click — hit effect at cursor
    F           — toggle fast/quality render mode
    ESC         — quit

Run from the repo root:
    python -m examples.example_particles
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.particles.emitter import Emitter
from pygame_engine.particles.presets import (
    explosion,
    fire_emitter,
    hit_effect,
    smoke,
    sparkle,
    trail,
)
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Stack


class ParticleExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app      = app
        self._fast:    bool          = False
        self._effects: list[Emitter] = []   # one-shot effects

        # Continuous emitters
        self._fire:  Emitter | None = None
        self._smoke: Emitter | None = None
        self._trail: Emitter | None = None

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        theme  = get_theme()

        # ── Hint labels ───────────────────────────────────────────────────────
        hints = [
            "Left click — explosion + sparkle",
            "Right click — hit effect",
            "F — toggle fast/quality render",
            "ESC — quit",
        ]
        root = Stack(pygame.Rect(screen))
        for i, hint in enumerate(hints):
            rect = pygame.Rect(12, 12 + i * 22, 400, 20)
            root.add(Label(rect, hint,
                           font_size=theme.typography.xs,
                           colour=theme.colours.text_secondary))

        # Render mode label
        self._mode_label = Label(
            anchor(screen, (300, 22), "top_right", margin=12),
            "Quality render",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            align="right",
        )
        root.add(self._mode_label)
        self.root_widget = root

        # ── Continuous emitters ───────────────────────────────────────────────
        cx, cy = screen.centerx, screen.centery

        # Fire — starts at centre, follows mouse
        self._fire = fire_emitter(cx, cy, rate=40)
        self._fire.start()

        # Smoke — fixed bottom-left corner
        self._smoke = smoke(80, screen.height - 40, rate=6)
        self._smoke.start()

        # Trail — follows mouse
        self._trail = trail(cx, cy, rate=25,
                            colour=((100, 160, 255), (180, 220, 255)))  # type: ignore
        self._trail.start()

    def on_exit(self) -> None:
        pass

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager

        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True

        # Toggle render mode
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            self._fast = not self._fast
            self._mode_label.text = (
                "Fast render (no alpha)" if self._fast else "Quality render"
            )
            return True

        # Left click — explosion + sparkle
        if inp.was_mouse_pressed(1):
            mx, my = inp.get_mouse_pos()
            ex = explosion(mx, my)
            ex.burst(55)
            self._effects.append(ex)

            sp = sparkle(mx, my)
            sp.burst(20)
            self._effects.append(sp)
            return True

        # Right click — hit effect
        if inp.was_mouse_pressed(3):
            mx, my = inp.get_mouse_pos()
            hx = hit_effect(mx, my, colour=(255, 220, 60), count=16)
            hx.burst(16)
            self._effects.append(hx)
            return True

        return False

    def update(self, dt: float) -> None:
        pygame.display.set_caption(
            f"pygame_engine — particles  |  "
            f"FPS: {self._app.clock.get_fps():.0f}  |  "
            f"particles: {self._total_particles()}"
        )

        mx, my = self._app.input_manager.get_mouse_pos()

        # Update continuous emitters and follow mouse
        if self._fire is not None:
            self._fire.x = mx
            self._fire.y = my + 20   # slightly below cursor
            self._fire.update(dt)

        if self._smoke is not None:
            self._smoke.update(dt)

        if self._trail is not None:
            self._trail.x = mx
            self._trail.y = my
            self._trail.update(dt)

        # Update one-shot effects and cull dead ones
        for fx in self._effects:
            fx.update(dt)
        self._effects = [fx for fx in self._effects if not fx.is_empty]

        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((12, 12, 18))   # very dark background

        # Render all particles
        render = "render_fast" if self._fast else "render"

        if self._smoke is not None:
            getattr(self._smoke, render)(surface)
        if self._trail is not None:
            getattr(self._trail, render)(surface)
        for fx in self._effects:
            getattr(fx, render)(surface)
        if self._fire is not None:
            getattr(self._fire, render)(surface)   # fire on top

        super().render(surface)   # UI labels on top of everything

    def _total_particles(self) -> int:
        total = 0
        for fx in (self._fire, self._smoke, self._trail):
            if fx is not None:
                total += fx.particle_count
        for fx in self._effects:
            total += fx.particle_count
        return total


def run() -> None:
    config = AppConfig(
        title="pygame_engine — particles",
        width=1280,
        height=720,
        resizable=True,
        target_fps=60,
    )
    app = Application(config)
    app.run(ParticleExampleScene(app))


if __name__ == "__main__":
    run()
