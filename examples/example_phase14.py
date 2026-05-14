"""
Phase 14 widget showcase — ListView, Badge, IntStepper, LogPanel,
KeyValuePanel, and ConfirmDialog.

What this example shows
-----------------------
Left column — ListView with a roster of heroes:
  - Custom row_renderer with Badge chips for class and status
  - Click to select; selection shown in KeyValuePanel below

Right column — LogPanel with live event log:
  - Every action (select, stepper change, confirm) appended

Centre panel — IntStepper, Badge strip, and KeyValuePanel:
  - IntStepper adjusts a "contract campaigns" value
  - Badge strip shows all five semantic styles
  - KeyValuePanel shows details for the selected hero

Confirm dialog:
  - "Dismiss Hero" button pushes a ConfirmDialog overlay
  - Demonstrates the lazy-push, modal-overlay pattern

Controls
--------
    Arrow keys / mouse wheel — scroll ListView
    Click a row              — select hero
    ESC                      — quit (with ConfirmDialog if hero selected)

Run from the repo root:
    python -m examples.example_phase14
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column, row
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import (
    Badge,
    Button,
    IntStepper,
    KeyValuePanel,
    Label,
    ListView,
    LogPanel,
    Panel,
    Stack,
)
from pygame_engine.ui.feedback.confirm_dialog import ConfirmDialog


# ── Fake data ─────────────────────────────────────────────────────────────────

_CLASSES   = ["Warrior", "Ranger", "Mage", "Rogue", "Cleric", "Paladin"]
_STATUSES  = ["Active", "Injured", "Expiring", "Low Morale", "Ready"]
_STATUS_STYLES = {
    "Active":     "good",
    "Injured":    "danger",
    "Expiring":   "warning",
    "Low Morale": "warning",
    "Ready":      "info",
}


@dataclass
class Hero:
    name:       str
    hero_class: str
    level:      int
    power:      int
    status:     str
    satisfaction: int

    def __str__(self) -> str:
        return self.name


def _make_roster(n: int = 14) -> list[Hero]:
    first = ["Aldric", "Kira", "Thorn", "Vael", "Orin", "Sylva",
             "Dusk",   "Rael", "Mira",  "Cael", "Bryn", "Skar",
             "Lyss",   "Dorn", "Wren",  "Hale"]
    rng = random.Random(42)
    heroes = []
    for i in range(n):
        heroes.append(Hero(
            name        = first[i % len(first)],
            hero_class  = rng.choice(_CLASSES),
            level       = rng.randint(1, 12),
            power       = rng.randint(20, 150),
            status      = rng.choice(_STATUSES),
            satisfaction= rng.randint(20, 100),
        ))
    return heroes


# ── Row renderer ──────────────────────────────────────────────────────────────

def _draw_hero_row(
    surface:  pygame.Surface,
    hero:     Hero,
    rect:     pygame.Rect,
    selected: bool,
    hovered:  bool,
) -> None:
    theme = get_theme()

    # Background
    if selected:
        bg, border = (55, 55, 80),  (140, 140, 210)
    elif hovered:
        bg, border = (42, 42, 58),  (90,  90, 120)
    else:
        bg, border = (32, 32, 44),  (60,  60,  80)
    pygame.draw.rect(surface, bg,     rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, 1, border_radius=6)

    # Name + level
    font_md = pygame.font.SysFont(theme.typography.family, theme.typography.md)
    font_sm = pygame.font.SysFont(theme.typography.family, theme.typography.sm)
    name_surf = font_md.render(
        f"{hero.name}  Lv {hero.level}", True, theme.colours.text)
    surface.blit(name_surf, (rect.x + 12, rect.y + 8))

    # Sub-line
    sub = font_sm.render(
        f"Power {hero.power}  •  Satisfaction {hero.satisfaction}",
        True, theme.colours.text_secondary)
    surface.blit(sub, (rect.x + 12, rect.y + 34))

    # Class badge
    class_badge = Badge(
        pygame.Rect(rect.right - 198, rect.y + 10, 90, 24),
        hero.hero_class, style="info",
    )
    class_badge.render(surface)

    # Status badge
    status_badge = Badge(
        pygame.Rect(rect.right - 98, rect.y + 10, 88, 24),
        hero.status, style=_STATUS_STYLES.get(hero.status, "default"),
    )
    status_badge.render(surface)


# ── Scene ─────────────────────────────────────────────────────────────────────

class Phase14Scene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app     = app
        self._roster  = _make_roster()
        self._log:    LogPanel    | None = None
        self._lv:     ListView    | None = None
        self._kv:     KeyValuePanel | None = None
        self._stepper: IntStepper | None = None

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()
        root  = Stack(pygame.Rect(screen))

        # ── Title bar ─────────────────────────────────────────────────────────
        root.add(Label(
            anchor(screen, (600, 36), "top", margin=18),
            "Phase 14 — ListView · Badge · IntStepper · LogPanel · KeyValuePanel · ConfirmDialog",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            align="center",
        ))

        # ── Left: ListView ────────────────────────────────────────────────────
        lv_rect = pygame.Rect(30, 72, 640, screen.height - 100)
        self._lv = ListView(
            rect=lv_rect,
            row_height=64,
            row_gap=6,
            padding=8,
            on_select=self._on_hero_selected,
        )
        self._lv.row_renderer = _draw_hero_row
        self._lv.set_items(self._roster)
        root.add(self._lv)

        # ── Centre: controls stack ────────────────────────────────────────────
        cx = 700

        # IntStepper
        self._stepper = IntStepper(
            rect=pygame.Rect(cx, 82, 260, 68),
            value=1, min_value=1, max_value=8,
            label="Contract Campaigns",
            fmt="{v} campaign(s)",
            on_change=self._on_stepper_change,
        )
        root.add(self._stepper)

        # Badge strip
        badge_y = 170
        for i, (text, style) in enumerate([
            ("default", "default"), ("info",    "info"),
            ("good",    "good"),    ("warning", "warning"),
            ("danger",  "danger"),
        ]):
            root.add(Badge(
                pygame.Rect(cx + i * 104, badge_y, 96, 28),
                text, style=style,
            ))

        # KeyValuePanel
        self._kv = KeyValuePanel(
            rect=pygame.Rect(cx, 216, 560, 340),
            title="Hero Details",
            rows=[("No hero selected", "—")],
        )
        root.add(self._kv)

        # Dismiss button
        dismiss_btn = Button(
            pygame.Rect(cx, 570, 200, 44),
            "Dismiss Hero",
            on_click=self._on_dismiss_clicked,
        )
        root.add(dismiss_btn)

        # ── Right: LogPanel ───────────────────────────────────────────────────
        log_rect = pygame.Rect(
            screen.width - 370, 72, 340, screen.height - 100)
        self._log = LogPanel(
            rect=log_rect, max_lines=200, padding=12)
        self._log.append("Phase 14 example started.", colour=(140, 200, 140))
        self._log.append("Click a hero to see details.")
        self._log.append("Adjust the stepper to change campaign count.")
        self._log.append("Use 'Dismiss Hero' to test ConfirmDialog.")
        root.add(self._log)

        self.root_widget = root

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_hero_selected(self, hero: Hero) -> None:
        if self._kv:
            self._kv.set_rows([
                ("Name",         hero.name),
                ("Class",        hero.hero_class),
                ("Level",        hero.level),
                ("Power",        hero.power),
                ("Status",       hero.status),
                ("Satisfaction", f"{hero.satisfaction}/100"),
            ])
        if self._log:
            self._log.append(
                f"Selected: {hero.name} ({hero.hero_class} Lv {hero.level})",
                colour=(180, 210, 255),
            )

    def _on_stepper_change(self, value: int) -> None:
        if self._log:
            self._log.append(f"Campaigns set to {value}.")

    def _on_dismiss_clicked(self) -> None:
        hero = self._lv.selected_item if self._lv else None
        name = hero.name if hero else "no one"
        ConfirmDialog.push(
            app=self._app,
            message=f"Dismiss {name} from the roster?",
            confirm_label="Dismiss",
            on_confirm=lambda: self._do_dismiss(hero),
            on_cancel=lambda: self._log_msg("Dismissal cancelled."),
            danger=True,
        )

    def _do_dismiss(self, hero) -> None:
        if hero and hero in self._roster:
            self._roster.remove(hero)
            if self._lv:
                self._lv.set_items(self._roster)
            if self._kv:
                self._kv.set_rows([("No hero selected", "—")])
            self._log_msg(f"Dismissed {hero.name}.", colour=(255, 160, 160))
        else:
            self._log_msg("No hero to dismiss.")

    def _log_msg(self, msg: str, colour=None) -> None:
        if self._log:
            self._log.append(msg, colour=colour)

    # ── Input ─────────────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((22, 22, 30))
        super().render(surface)


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — Phase 14 widgets",
        width=1400, height=820,
        resizable=True, target_fps=60,
    ))
    app.run(Phase14Scene(app))


if __name__ == "__main__":
    run()
