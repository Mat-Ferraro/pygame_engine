"""
What this example shows:
- Tween with multiple easing functions side by side
- SpriteAnimation frame cycling (coloured placeholder frames)
- AnimationPlayer play/stop/switch
- AnimationStateMachine idle/run/jump driven by keyboard input

Controls:
    Arrow keys / WASD — move the character (triggers run state)
    Space             — jump (triggers jump state)
    ESC               — quit

Run from the repo root:
    python -m examples.example_animation
"""

from __future__ import annotations

import math

import pygame

from pygame_engine.animation import (
    AnimationPlayer,
    AnimationStateMachine,
    SpriteAnimation,
    Tween,
)
from pygame_engine.animation.easing import (
    ease_in_out_cubic,
    ease_out_back,
    ease_out_bounce,
    ease_out_elastic,
    linear,
)
from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Stack


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_frame(colour: tuple, size: tuple = (48, 64)) -> pygame.Surface:
    s = pygame.Surface(size)
    s.fill(colour)
    pygame.draw.rect(s, tuple(min(255, c + 40) for c in colour),
                     s.get_rect(), width=2)
    return s


def _make_anim(name: str, colours: list, duration: float = 0.12) -> SpriteAnimation:
    frames = [_make_frame(c) for c in colours]
    return SpriteAnimation(name, frames, frame_duration=duration, loop=True)


# ── Tween demo row ────────────────────────────────────────────────────────────

class _TweenBar:
    """One row of the tween demo — label + animated dot."""
    W = 400

    def __init__(self, x: int, y: int, label: str, easing, colour: tuple):
        self.x      = x
        self.y      = y
        self.label  = label
        self.colour = colour
        self._tween = Tween(0, self.W, duration=1.6, easing=easing,
                            loop=True, auto_start=True)

    def update(self, dt: float) -> None:
        self._tween.update(dt)

    def render(self, surface: pygame.Surface, font: pygame.font.Font,
               theme) -> None:
        # Track line
        pygame.draw.line(surface, theme.colours.border,
                         (self.x, self.y), (self.x + self.W, self.y), 1)
        # Dot
        dot_x = self.x + int(self._tween.value)
        pygame.draw.circle(surface, self.colour, (dot_x, self.y), 7)
        # Label
        surf = font.render(self.label, True, theme.colours.text_secondary)
        surface.blit(surf, (self.x + self.W + 12, self.y - surf.get_height() // 2))


# ── Scene ─────────────────────────────────────────────────────────────────────

class AnimationExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        # ── Tween bars ────────────────────────────────────────────────────────
        easings = [
            ("linear",          linear,            (100, 160, 240)),
            ("ease_out_back",   ease_out_back,      (100, 220, 140)),
            ("ease_out_bounce", ease_out_bounce,    (220, 160, 80)),
            ("ease_out_elastic",ease_out_elastic,   (220, 100, 160)),
            ("ease_in_out_cubic",ease_in_out_cubic, (160, 100, 220)),
        ]
        start_x = 80
        start_y = 80
        self._bars = [
            _TweenBar(start_x, start_y + i * 44, name, ease, col)
            for i, (name, ease, col) in enumerate(easings)
        ]

        # ── AnimationPlayer + StateMachine ────────────────────────────────────
        player = AnimationPlayer()
        player.add("idle", _make_anim("idle",
            [(60, 100, 180), (70, 110, 190)], duration=0.5))
        player.add("run",  _make_anim("run",
            [(60, 160, 80), (80, 200, 100), (60, 160, 80), (40, 130, 60)],
            duration=0.1))
        player.add("jump", _make_anim("jump",
            [(200, 160, 60)], duration=0.2))

        sm = AnimationStateMachine(player)
        sm.add_state("idle", default=True)
        sm.add_state("run")
        sm.add_state("jump")
        sm.add_transition("idle", "run",  lambda p: abs(p.get("vx", 0)) > 0)
        sm.add_transition("run",  "idle", lambda p: abs(p.get("vx", 0)) == 0)
        sm.add_transition("idle", "jump", lambda p: p.get("jumping", False))
        sm.add_transition("run",  "jump", lambda p: p.get("jumping", False))
        sm.add_transition("jump", "idle", lambda p: p.get("landed", False))

        self._player    = player
        self._sm        = sm
        self._char_x    = float(screen.centerx)
        self._char_y    = float(screen.height - 140)
        self._vx        = 0.0
        self._vy        = 0.0
        self._on_ground = True
        self._jumping   = False
        self._ground_y  = screen.height - 140

        # ── Labels ────────────────────────────────────────────────────────────
        root = Stack(pygame.Rect(screen))
        root.add(Label(pygame.Rect(80, 20, 400, 28), "Tween Easings",
                       font_size=theme.typography.lg, colour=theme.colours.text))
        root.add(Label(
            anchor(screen, (500, 24), "bottom", margin=44),
            "Arrow/WASD = move   Space = jump   ESC = quit",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        ))
        self._state_label = Label(
            anchor(screen, (300, 22), "bottom", margin=16),
            "State: idle",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        )
        root.add(self._state_label)
        self.root_widget = root

        # Font for tween labels
        self._font = pygame.font.SysFont(theme.typography.family,
                                          theme.typography.xs)

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        return False

    def update(self, dt: float) -> None:
        inp = self._app.input_manager
        speed = 200.0
        self._vx = 0.0
        self._jumping = False

        if inp.is_action_down(actions.NAV_LEFT):  self._vx = -speed
        if inp.is_action_down(actions.NAV_RIGHT): self._vx =  speed
        if inp.was_key_pressed(pygame.K_SPACE) and self._on_ground:
            self._vy = -500.0; self._on_ground = False; self._jumping = True

        # Gravity — use a small floor-press velocity when grounded so
        # on_ground is reliably set every frame the player is on the floor.
        if self._on_ground:
            self._vy = 60.0
        else:
            self._vy = min(self._vy + 900 * dt, 800)
        self._char_y += self._vy * dt
        if self._char_y >= self._ground_y:
            self._char_y    = self._ground_y
            self._vy        = 0.0
            self._on_ground = True

        self._char_x += self._vx * dt
        self._char_x = max(40, min(self._app.screen_rect.width - 40,
                                    self._char_x))

        self._sm.update(dt, params={
            "vx":      self._vx,
            "jumping": self._jumping,
            "landed":  self._on_ground,
        })
        self._state_label.text = f"State: {self._sm.current_state}"

        for bar in self._bars:
            bar.update(dt)

        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        theme = get_theme()
        surface.fill(theme.colours.bg_base)

        # Ground line
        pygame.draw.line(surface, theme.colours.border,
                         (0, self._ground_y + 64),
                         (surface.get_width(), self._ground_y + 64), 1)

        # Character
        frame = self._player.current_frame
        if frame:
            r = frame.get_rect(centerx=int(self._char_x),
                                bottom=int(self._char_y) + 64)
            surface.blit(frame, r)
        else:
            pygame.draw.rect(surface, (80, 140, 220),
                             pygame.Rect(int(self._char_x) - 24,
                                         int(self._char_y), 48, 64),
                             border_radius=4)

        # Tween demo divider
        pygame.draw.line(surface, theme.colours.border,
                         (60, 60), (60, 320), 1)

        for bar in self._bars:
            bar.render(surface, self._font, theme)

        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — animation",
        width=1280, height=720,
    ))
    app.run(AnimationExampleScene(app))


if __name__ == "__main__":
    run()
