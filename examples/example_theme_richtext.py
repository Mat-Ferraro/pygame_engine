"""
What this example shows:
- theme_from_file() loading a JSON theme override
- reload_theme_file() hot-reload (press R)
- theme_to_dict() serialisation
- RichLabel with [b], [i], [color=#rrggbb], [size=N] tags
- Tags nested and combined
- Unknown tags rendered as literal text (never crash)
- Live theme switching (press D for dark, L for light)

Controls:
    R — hot-reload theme from file (edit assets/theme.json and press R)
    D — switch to built-in dark theme
    L — switch to built-in light-ish theme
    ESC — quit

Run from the repo root:
    python -m examples.example_theme_richtext
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene
from pygame_engine.theme.defaults import DEFAULT_THEME
from pygame_engine.theme.loader import theme_from_file, theme_to_dict
from pygame_engine.theme.runtime import get_theme, reset_theme, set_theme
from pygame_engine.ui import Label, Panel, Stack
from pygame_engine.ui.text.rich_label import RichLabel

# Look for theme.json relative to this file's directory (repo root),
# then fall back to game_template/assets/theme.json.
_HERE = Path(__file__).parent.parent   # repo root
THEME_PATH = _HERE / "assets" / "theme.json"
if not THEME_PATH.exists():
    THEME_PATH = _HERE / "game_template" / "assets" / "theme.json"

# A simple "light-ish" theme variant for the toggle demo
def _make_light_theme():
    t = deepcopy(DEFAULT_THEME)
    t.colours.bg_base    = (220, 220, 228)
    t.colours.bg_raised  = (200, 202, 215)
    t.colours.text       = (20, 20, 30)
    t.colours.text_secondary = (80, 80, 100)
    t.colours.border     = (160, 165, 190)
    t.button.normal.bg   = (100, 140, 220)
    return t


class ThemeRichTextScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._status: Label | None = None

    def on_enter(self) -> None:
        self._build_ui()

    def _build_ui(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        root = Stack(pygame.Rect(screen))

        # ── Title ─────────────────────────────────────────────────────────────
        root.add(Label(
            anchor(screen, (600, 36), "top", margin=24),
            "Theme & Rich Text Demo",
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        ))

        # ── RichLabel showcase panel ──────────────────────────────────────────
        panel_rect = anchor(screen, (820, 420), "center", offset=(-100, 0))
        panel      = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 12,
                        panel_rect.width - 32, 28),
            "RichLabel markup",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        rich_samples = [
            "Plain text — no markup",
            "[b]Bold text[/b]",
            "[i]Italic text[/i]",
            "[b][i]Bold italic[/i][/b]",
            "[color=#ff4444]Red text[/color]",
            "[color=#44ff88]Green text[/color]",
            "[color=#4488ff]Blue text[/color]",
            "[size=24]Larger text[/size]  [size=12]Smaller text[/size]",
            "[b]Score:[/b] [color=#ffd700]1 234 pts[/color]",
            "HP: [color=#ff4444]45[/color]/[color=#88ff88]100[/color]",
            "[color=#aaaaff][i]Status: [b]poisoned[/b][/i][/color]",
            "Unknown [blah]tag[/blah] renders literally",
        ]

        for i, sample in enumerate(rich_samples):
            y = panel_rect.y + 52 + i * 28
            panel.add(RichLabel(
                pygame.Rect(panel_rect.x + 16, y, panel_rect.width - 32, 26),
                sample,
                font_size=theme.typography.sm,
                colour=theme.colours.text,
                align="left",
            ))

        root.add(panel)

        # ── Theme info panel ──────────────────────────────────────────────────
        info_rect = anchor(screen, (300, 420), "right", margin=60,
                           offset=(0, 0))
        info_panel = Panel(info_rect)

        info_panel.add(Label(
            pygame.Rect(info_rect.x + 16, info_rect.y + 12,
                        info_rect.width - 32, 28),
            "Active theme",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        # Show key theme values
        d    = theme_to_dict(theme)
        rows = [
            f"bg_base:  {d['colours']['bg_base']}",
            f"text:     {d['colours']['text']}",
            f"family:   {d['typography']['family'][:20]}",
            f"md size:  {d['typography']['md']}",
            f"btn bg:   {d['button']['normal']['bg']}",
            f"btn rad:  {d['button']['normal']['radius']}",
            f"spacing.xl: {d['spacing']['xl']}",
        ]
        for i, row in enumerate(rows):
            info_panel.add(Label(
                pygame.Rect(info_rect.x + 16, info_rect.y + 52 + i * 26,
                             info_rect.width - 32, 22),
                row,
                font_size=theme.typography.xs,
                colour=theme.colours.text_secondary,
            ))

        # Theme file path note
        exists = THEME_PATH.exists()
        note = (f"theme.json: {'found ✓' if exists else 'not found'}")
        info_panel.add(Label(
            pygame.Rect(info_rect.x + 16, info_rect.bottom - 80,
                        info_rect.width - 32, 22),
            note,
            font_size=theme.typography.xs,
            colour=(100, 220, 100) if exists else theme.colours.text_secondary,
        ))

        root.add(info_panel)

        # ── Controls hint ─────────────────────────────────────────────────────
        hints = "R = reload theme.json   D = dark   L = light   ESC = quit"
        self._status = Label(
            anchor(screen, (700, 22), "bottom", margin=14),
            hints,
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            align="center",
        )
        root.add(self._status)

        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            reset_theme()
            self._app.stop()
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                if THEME_PATH.exists():
                    try:
                        set_theme(theme_from_file(THEME_PATH))
                        msg = "Reloaded theme from assets/theme.json"
                    except Exception as e:
                        msg = f"Reload failed: {e}"
                else:
                    msg = "assets/theme.json not found — using default"
                self._build_ui()
                if self._status:
                    self._status.text = msg
                return True

            if event.key == pygame.K_d:
                reset_theme()
                self._build_ui()
                return True

            if event.key == pygame.K_l:
                set_theme(_make_light_theme())
                self._build_ui()
                return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — theme & rich text",
        width=1280, height=720,
    ))
    app.run(ThemeRichTextScene(app))


if __name__ == "__main__":
    run()
