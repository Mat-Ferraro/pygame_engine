"""
Demonstrates Application extension hooks.

What this example shows:
- add_hook(name, callback, priority) — attach behaviour without subclassing
- Six hook points: startup, shutdown, pre_update, post_update,
  pre_render, post_render
- Priority ordering — higher number fires later
- remove_hook() — unregister a callback at runtime
- A simple analytics/logging module wired in via hooks

Two "modules" are demonstrated:
  FrameLogger  — logs dt every N frames using pre_update hook
  FpsOverlay   — draws a custom FPS bar using post_render hook

Controls:
    T         — toggle FrameLogger on/off (add/remove hook at runtime)
    ESC       — quit

Run from the repo root:
    python -m examples.example_hooks
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack


# ── Simulated extension modules ───────────────────────────────────────────────

class FrameLogger:
    """
    Logs delta-time every N frames via the pre_update hook.

    Demonstrates: a stateful module that registers/unregisters
    a hook at runtime via add_hook / remove_hook.
    """

    def __init__(self, app: Application, interval: int = 60) -> None:
        self._app      = app
        self._interval = interval
        self._frame    = 0
        self._log: list[str] = []
        self._enabled  = False

    def enable(self) -> None:
        if not self._enabled:
            self._app.add_hook("pre_update", self._on_pre_update, priority=0)
            self._enabled = True
            self._log.append("FrameLogger enabled")

    def disable(self) -> None:
        if self._enabled:
            self._app.remove_hook("pre_update", self._on_pre_update)
            self._enabled = False
            self._log.append("FrameLogger disabled")

    def toggle(self) -> None:
        self.disable() if self._enabled else self.enable()

    def _on_pre_update(self, dt: float) -> None:
        self._frame += 1
        if self._frame % self._interval == 0:
            self._log.append(f"  frame {self._frame:5d}  dt={dt*1000:.1f}ms")
        # Keep last 8 lines
        if len(self._log) > 8:
            self._log = self._log[-8:]

    @property
    def log(self) -> list[str]:
        return list(self._log)

    @property
    def enabled(self) -> bool:
        return self._enabled


class FpsBarOverlay:
    """
    Draws a thin FPS bar at the top of the screen via post_render hook.

    Demonstrates: a rendering overlay that attaches via post_render
    with high priority so it draws on top of everything.
    """

    def __init__(self, app: Application) -> None:
        self._app    = app
        self._target = app.config.target_fps or 60
        app.add_hook("post_render", self._draw, priority=100)

    def _draw(self, surface: pygame.Surface) -> None:
        tm  = self._app.time
        dt  = tm.unscaled_delta_time
        fps = 1.0 / dt if dt > 0 else 0.0
        ratio   = min(fps / self._target, 1.0)
        bar_w   = int(surface.get_width() * ratio)
        colour  = (
            (60, 200, 80)   if ratio > 0.8 else
            (220, 180, 40)  if ratio > 0.5 else
            (220, 60, 60)
        )
        pygame.draw.rect(surface, colour, pygame.Rect(0, 0, bar_w, 4))


# ── Scene ─────────────────────────────────────────────────────────────────────

class HooksScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._logger = FrameLogger(app, interval=30)
        self._fps_bar = FpsBarOverlay(app)
        self._log_label: Label | None = None
        self._toggle_btn: Button | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        # Start logger enabled
        self._logger.enable()

        panel_rect = anchor(screen, (600, 520), "center")
        panel = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 14,
                        panel_rect.width - 32, 32),
            "Extension Hooks Demo",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))
        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 50,
                        panel_rect.width - 32, 22),
            "FpsBar: post_render hook (priority 100)  |  "
            "FrameLogger: pre_update hook (priority 0)",
            font_size=theme.typography.xs, colour=theme.colours.text_secondary,
        ))

        btn_rects = column(
            pygame.Rect(panel_rect.x, panel_rect.y + 84,
                        panel_rect.width, 120),
            count=2, item_size=(panel_rect.width - 32, 44), spacing=10,
            padding=theme.spacing.lg,
        )

        self._toggle_btn = Button(
            btn_rects[0], "Disable FrameLogger (T)",
            on_click=self._toggle_logger,
        )
        panel.add(self._toggle_btn)
        panel.add(Button(btn_rects[1], "Quit (ESC)", on_click=self._app.stop))

        self._log_label = Label(
            pygame.Rect(panel_rect.x + 16, btn_rects[1].bottom + 16,
                        panel_rect.width - 32, 200),
            "",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
        )
        panel.add(self._log_label)

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        self.root_widget = root

    def _toggle_logger(self) -> None:
        self._logger.toggle()
        if self._toggle_btn:
            state = "Disable" if self._logger.enabled else "Enable"
            self._toggle_btn.label = f"{state} FrameLogger (T)"

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._log_label:
            self._log_label.text = "\n".join(self._logger.log)

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self._toggle_logger(); return True
            if event.key == pygame.K_ESCAPE:
                self._app.stop(); return True
        return False

    def render(self, surface: pygame.Surface, ctx=None) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface, ctx)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — Extension Hooks",
        width=1280, height=720, resizable=True,
    ))
    app.run(HooksScene(app))


if __name__ == "__main__":
    run()
