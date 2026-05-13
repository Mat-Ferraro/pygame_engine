"""
Demonstrates AudioManager — music, SFX, volume, and mute.

What this example shows:
- AudioManager.master_volume / music_volume / sfx_volume sliders
- toggle_mute()
- play_music() / stop_music() / pause_music() / resume_music()
- play_sfx() with a generated click sound (no asset files required)
- Volume slider wired to AudioManager properties
- Live mute toggle

Note: No real audio files are needed — the example generates a short
      sine-wave click sound procedurally using pygame.sndarray.

Controls:
    Click sliders to adjust volume
    M     — toggle mute
    ESC   — quit

Run from the repo root:
    python -m examples.example_audio
"""

from __future__ import annotations

import math

import numpy as np
import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.ui.controls.slider import Slider


def _make_click_sound(freq: float = 440.0, duration_ms: int = 80) -> pygame.mixer.Sound:
    """Generate a short sine-wave tone as a pygame Sound."""
    sample_rate = 44100
    n_samples   = int(sample_rate * duration_ms / 1000)
    t           = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    wave        = (np.sin(2 * math.pi * freq * t) * 32767 * 0.4).astype(np.int16)
    # Fade out to avoid click artefact
    fade        = np.linspace(1.0, 0.0, n_samples)
    wave        = (wave * fade).astype(np.int16)
    stereo      = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(stereo)


def _make_tone_sound(freq: float = 220.0, duration_ms: int = 400) -> pygame.mixer.Sound:
    sample_rate = 44100
    n_samples   = int(sample_rate * duration_ms / 1000)
    t           = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    wave        = (np.sin(2 * math.pi * freq * t) * 32767 * 0.3).astype(np.int16)
    fade_in     = np.linspace(0.0, 1.0, n_samples // 4)
    fade_out    = np.linspace(1.0, 0.0, n_samples)
    envelope    = np.ones(n_samples)
    envelope[:len(fade_in)]  *= fade_in
    envelope[-len(fade_in):] *= fade_in[::-1]
    wave        = (wave * envelope).astype(np.int16)
    stereo      = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(stereo)


class AudioExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._click  = None
        self._tone   = None
        self._status: Label | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()
        audio  = self._app.audio

        # Generate sounds (no files needed)
        try:
            self._click = _make_click_sound(880, 60)
            self._tone  = _make_tone_sound(330, 500)
            sounds_ok   = True
        except Exception as e:
            sounds_ok = False
            print(f"[audio example] numpy not available or sndarray error: {e}")

        # ── Panel ─────────────────────────────────────────────────────────────
        panel_rect = anchor(screen, (460, 480), "center")
        panel      = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 12,
                        panel_rect.width - 32, 28),
            "AudioManager Demo",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        # Volume sliders
        def row_label(y: int, text: str) -> Label:
            return Label(
                pygame.Rect(panel_rect.x + 16, y, 140, 30),
                text, font_size=theme.typography.sm,
                colour=theme.colours.text_secondary,
            )

        slider_x = panel_rect.x + 170
        slider_w = panel_rect.width - 200

        volumes = [
            ("Master vol",  audio.master_volume,
             lambda v: setattr(audio, "master_volume", v)),
            ("Music vol",   audio.music_volume,
             lambda v: setattr(audio, "music_volume", v)),
            ("SFX vol",     audio.sfx_volume,
             lambda v: setattr(audio, "sfx_volume", v)),
        ]
        for i, (label, val, cb) in enumerate(volumes):
            y = panel_rect.y + 60 + i * 52
            panel.add(row_label(y + 8, label))
            panel.add(Slider(
                pygame.Rect(slider_x, y + 8, slider_w, 26),
                value=val, on_change=cb,
            ))

        # Buttons
        btn_rects = column(
            pygame.Rect(panel_rect.x, panel_rect.y + 230,
                        panel_rect.width, 240),
            count=5, item_size=(320, 44), spacing=8,
            padding=theme.spacing.lg,
        )

        panel.add(Button(btn_rects[0], "Play click SFX",
                          on_click=self._play_click))
        panel.add(Button(btn_rects[1], "Play tone SFX",
                          on_click=self._play_tone))
        panel.add(Button(btn_rects[2], "Toggle mute (M)",
                          on_click=audio.toggle_mute))
        panel.add(Button(btn_rects[3], "Quit",
                          on_click=self._app.stop))

        # Status
        self._status = Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.bottom - 48,
                        panel_rect.width - 32, 28),
            "Ready" if sounds_ok else "numpy unavailable — sliders work, sounds skip",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
        )
        panel.add(self._status)

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(Label(
            anchor(screen, (400, 22), "bottom", margin=14),
            "M = mute   ESC = quit",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        ))
        self.root_widget = root

    def _play_click(self) -> None:
        if self._click:
            self._app.audio.play_sfx(self._click)
            self._set_status("Played click SFX")

    def _play_tone(self) -> None:
        if self._tone:
            self._app.audio.play_sfx(self._tone)
            self._set_status("Played tone SFX")

    def _set_status(self, msg: str) -> None:
        if self._status:
            muted = self._app.audio.muted
            self._status.text = f"{msg}{'  [MUTED]' if muted else ''}"

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self._app.audio.toggle_mute()
            self._set_status("Mute toggled")
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — audio",
        width=1280, height=720,
        resizable=True,
    ))
    app.run(AudioExampleScene(app))


if __name__ == "__main__":
    run()
