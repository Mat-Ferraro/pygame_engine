"""
What this example shows:
- FadeTransition (configurable duration and colour)
- SlideTransition in all four directions
- CrossfadeTransition between scenes
- push_with / replace_with / pop_with
- Overlay scene on top with semi-transparent background

Controls:
    Buttons or number keys 1-6 — trigger each transition type
    P — push overlay scene on top
    ESC — quit (or close overlay)

Run from the repo root:
    python -m examples.example_transitions
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import (
    CrossfadeTransition,
    FadeTransition,
    Scene,
    SlideTransition,
)
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack


# Two alternating background colours so the transition is visually obvious
BG_A = (22, 28, 46)
BG_B = (28, 44, 28)


class TransitionMenuScene(Scene):
    blocks_input_below = blocks_update_below = blocks_render_below = True

    def __init__(self, app: Application, bg: tuple = BG_A) -> None:
        super().__init__()
        self._app = app
        self._bg  = bg

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()
        next_bg = BG_B if self._bg == BG_A else BG_A

        panel_rect = anchor(screen, (400, 460), "center")
        panel      = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x, panel_rect.y - 52,
                        panel_rect.width, 40),
            "Scene Transitions",
            font_size=theme.typography.xl,
            colour=theme.colours.text, align="center",
        ))

        transitions = [
            ("1 — Fade (0.5s)",         lambda: FadeTransition(0.5)),
            ("2 — Slide Left  →",       lambda: SlideTransition(0.4, "left")),
            ("3 — Slide Right ←",       lambda: SlideTransition(0.4, "right")),
            ("4 — Slide Up    ↑",       lambda: SlideTransition(0.4, "up")),
            ("5 — Slide Down  ↓",       lambda: SlideTransition(0.4, "down")),
            ("6 — Crossfade",           lambda: CrossfadeTransition(0.5)),
            ("P — Push overlay",        None),
            ("Quit",                    None),
        ]

        rects = column(panel_rect, count=len(transitions),
                       item_size=(320, 44), spacing=6,
                       padding=theme.spacing.xl)

        for i, (label, trans_fn) in enumerate(transitions):
            if label == "Quit":
                panel.add(Button(rects[i], label, on_click=self._app.stop))
                continue
            if trans_fn is None:
                panel.add(Button(
                    rects[i], label,
                    on_click=lambda: self._app.scene_manager.push_with(
                        _OverlayScene(self._app),
                        FadeTransition(0.25),
                    ),
                ))
                continue

            def make_cb(tfn=trans_fn, nbg=next_bg):
                def cb():
                    self._app.scene_manager.replace_with(
                        TransitionMenuScene(self._app, nbg), tfn()
                    )
                return cb
            panel.add(Button(rects[i], label, on_click=make_cb()))

        panel.add(Label(
            anchor(screen, (400, 22), "bottom", margin=14),
            "Number keys 1-6 also work   •   ESC = quit",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        ))

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        sm  = self._app.scene_manager
        nbg = BG_B if self._bg == BG_A else BG_A
        if event.type == pygame.KEYDOWN:
            mapping = {
                pygame.K_1: lambda: FadeTransition(0.5),
                pygame.K_2: lambda: SlideTransition(0.4, "left"),
                pygame.K_3: lambda: SlideTransition(0.4, "right"),
                pygame.K_4: lambda: SlideTransition(0.4, "up"),
                pygame.K_5: lambda: SlideTransition(0.4, "down"),
                pygame.K_6: lambda: CrossfadeTransition(0.5),
            }
            if event.key in mapping:
                sm.replace_with(TransitionMenuScene(self._app, nbg),
                                 mapping[event.key]())
                return True
            if event.key == pygame.K_p:
                sm.push_with(_OverlayScene(self._app), FadeTransition(0.25))
                return True
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(self._bg)
        super().render(surface)


class _OverlayScene(Scene):
    blocks_input_below = True
    blocks_render_below = False

    def __init__(self, app: Application) -> None:
        super().__init__(); self._app = app

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()
        # Panel is tall enough for title + body text + button with breathing room
        panel  = Panel(anchor(screen, (400, 220), "center"))
        px, py = panel.rect.x, panel.rect.y
        pw     = panel.rect.width

        panel.add(Label(
            pygame.Rect(px + 16, py + 20, pw - 32, 32),
            "Overlay (push/pop)",
            font_size=theme.typography.lg,
            colour=theme.colours.text, align="center",
        ))

        panel.add(Label(
            pygame.Rect(px + 16, py + 64, pw - 32, 44),
            "Background scene is still visible below.",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary, align="center",
        ))

        close_rect = pygame.Rect(px + (pw - 240) // 2, py + 152, 240, 44)
        panel.add(Button(close_rect, "Close (ESC)",
                          on_click=lambda: self._app.scene_manager.pop_with(
                              FadeTransition(0.25))))

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.scene_manager.pop_with(FadeTransition(0.25)); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 160))
        surface.blit(shade, (0, 0))
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — transitions",
        width=1280, height=720,
    ))
    app.run(TransitionMenuScene(app))


if __name__ == "__main__":
    run()
