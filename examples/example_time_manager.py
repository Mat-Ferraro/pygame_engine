"""
Demonstrates TimeManager — pause, slow-motion, and fixed-step callbacks.

What this example shows:
- app.time.time_scale.value = 0.0  →  pauses all scaled game logic
- app.time.time_scale.value = 0.5  →  half speed
- app.time.time_scale.value = 2.0  →  double speed
- unscaled_time always advances regardless of time_scale
- register_fixed_step() fires at a fixed Hz even during slow-mo
- Subscribing to time_scale changes to react to pause/resume

A ball bounces across the screen driven by scaled delta_time.
The fixed-step counter fires at 10 Hz regardless of time_scale.

Controls:
    SPACE     — toggle pause (time_scale 0 ↔ 1)
    S         — slow motion (time_scale = 0.3)
    F         — fast forward (time_scale = 3.0)
    R         — reset to normal (time_scale = 1.0)
    ESC       — quit

Run from the repo root:
    python -m examples.example_time_manager
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.ui.text.text_block import TextBlock


class Ball:
    """A simple bouncing ball driven by scaled time."""

    def __init__(self, screen_rect: pygame.Rect) -> None:
        self._bounds = screen_rect
        self._x   = float(screen_rect.centerx)
        self._y   = float(screen_rect.centery)
        self._vx  = 280.0   # pixels / second
        self._vy  = 190.0
        self.radius = 18
        self.colour = (80, 160, 240)

    def update(self, dt: float) -> None:
        """Advance using scaled dt — pauses when time_scale == 0."""
        self._x += self._vx * dt
        self._y += self._vy * dt

        if self._x - self.radius < self._bounds.left:
            self._x = self._bounds.left + self.radius
            self._vx = abs(self._vx)
        elif self._x + self.radius > self._bounds.right:
            self._x = self._bounds.right - self.radius
            self._vx = -abs(self._vx)

        if self._y - self.radius < self._bounds.top:
            self._y = self._bounds.top + self.radius
            self._vy = abs(self._vy)
        elif self._y + self.radius > self._bounds.bottom:
            self._y = self._bounds.bottom - self.radius
            self._vy = -abs(self._vy)

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.colour,
                           (int(self._x), int(self._y)), self.radius)
        pygame.draw.circle(surface, (200, 230, 255),
                           (int(self._x), int(self._y)), self.radius, 2)


class TimeManagerScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app         = app
        self._fixed_ticks = 0
        self._status: Label | None = None
        self._ball: Ball | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        # ── Ball area (left two-thirds) ───────────────────────────────────────
        ball_area = pygame.Rect(
            screen.x, screen.y,
            screen.width * 2 // 3, screen.height,
        )
        self._ball = Ball(ball_area.inflate(-40, -120))

        # ── Control panel (right third) ───────────────────────────────────────
        panel_rect = pygame.Rect(
            ball_area.right, screen.top,
            screen.width - ball_area.width, screen.height,
        )
        panel = Panel(panel_rect)

        title = Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 16,
                        panel_rect.width - 32, 32),
            "TimeManager Demo",
            font_size=theme.typography.lg,
            colour=theme.colours.text,
        )
        panel.add(title)

        btn_rects = column(
            pygame.Rect(panel_rect.x, panel_rect.y + 68,
                        panel_rect.width, 340),
            count=6, item_size=(panel_rect.width - 32, 44), spacing=10,
            padding=theme.spacing.lg,
        )

        tm = self._app.time

        def set_scale(v: float):
            tm.time_scale.value = v

        panel.add(Button(btn_rects[0], "Pause / Resume (SPACE)",
                         on_click=self._toggle_pause))
        panel.add(Button(btn_rects[1], "Slow motion ×0.3 (S)",
                         on_click=lambda: set_scale(0.3)))
        panel.add(Button(btn_rects[2], "Normal speed ×1.0 (R)",
                         on_click=lambda: set_scale(1.0)))
        panel.add(Button(btn_rects[3], "Fast forward ×3.0 (F)",
                         on_click=lambda: set_scale(3.0)))
        panel.add(Button(btn_rects[4], "Quit (ESC)",
                         on_click=self._app.stop))

        self._status = Label(
            pygame.Rect(panel_rect.x + 16, btn_rects[4].bottom + 20,
                        panel_rect.width - 32, 120),
            "Ready",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
        )
        panel.add(self._status)

        # Subscribe to time_scale changes
        self.subscriptions.on(
            tm.time_scale,
            lambda old, new: self._on_scale_change(new),
        )

        # Fixed-step at 10 Hz — counts ticks regardless of time_scale
        # (fixed_step uses scaled time, so it also pauses when paused)
        tm.register_fixed_step(self._fixed_tick, rate=10)

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        self.root_widget = root

    def _toggle_pause(self) -> None:
        tm = self._app.time
        if tm.time_scale.value == 0.0:
            tm.time_scale.value = 1.0
        else:
            tm.time_scale.value = 0.0

    def _on_scale_change(self, new_scale: float) -> None:
        """React to time_scale changes — update status label."""
        if self._status:
            state = "PAUSED" if new_scale == 0.0 else f"×{new_scale:.1f}"
            self._status.text = f"time_scale: {state}"

    def _fixed_tick(self) -> None:
        self._fixed_ticks += 1

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._ball:
            self._ball.update(dt)   # dt is already scaled

        # Update status with live time values
        if self._status:
            tm = self._app.time
            scale = tm.time_scale.value
            state = "PAUSED" if scale == 0.0 else f"×{scale:.1f}"
            self._status.text = (
                f"time_scale: {state}\n"
                f"scaled time:   {tm.time:.2f}s\n"
                f"unscaled time: {tm.unscaled_time:.2f}s\n"
                f"frame:         {tm.frame_count}\n"
                f"fixed ticks:   {self._fixed_ticks}"
            )

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            tm = self._app.time
            if event.key == pygame.K_SPACE:
                self._toggle_pause(); return True
            if event.key == pygame.K_s:
                tm.time_scale.value = 0.3; return True
            if event.key == pygame.K_r:
                tm.time_scale.value = 1.0; return True
            if event.key == pygame.K_f:
                tm.time_scale.value = 3.0; return True
            if event.key == pygame.K_ESCAPE:
                self._app.stop(); return True
        return False

    def render(self, surface: pygame.Surface, ctx=None) -> None:
        theme = get_theme()
        surface.fill(theme.colours.bg_base)
        if self._ball:
            self._ball.render(surface)
        super().render(surface, ctx)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — TimeManager",
        width=1280, height=720, resizable=True,
    ))
    app.run(TimeManagerScene(app))


if __name__ == "__main__":
    run()
