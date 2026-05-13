"""
What this example shows:
- SaveManager save/load/exists/delete/list_slots
- Saving arbitrary payload dicts
- Displaying saved metadata (slot name, timestamp)
- Confirming loaded data matches what was saved
- Slot management (overwrite, delete)

Controls:
    Click buttons to interact
    ESC — quit

Run from the repo root:
    python -m examples.example_persistence
"""

from __future__ import annotations

from pathlib import Path

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.persistence import SaveManager
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.ui.text.text_block import TextBlock

SAVE_DIR  = Path("saves_example")
SAVE_SLOT = "player_save"


class PersistenceExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app     = app
        self._manager = SaveManager(save_dir=SAVE_DIR, game_id="example_persistence")
        self._log_label: TextBlock | None = None
        self._log_lines: list[str] = []
        self._score = 0

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        # ── Button panel ──────────────────────────────────────────────────────
        panel_rect = anchor(screen, (320, 480), "left", margin=60)
        panel      = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 12,
                        panel_rect.width - 32, 28),
            "SaveManager Demo",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        btn_rects = column(panel_rect, count=6, item_size=(260, 44),
                           spacing=8, padding=theme.spacing.xxl)
        panel.add(Button(btn_rects[0], "Save (slot: player_save)",
                          on_click=self._do_save))
        panel.add(Button(btn_rects[1], "Load",
                          on_click=self._do_load))
        panel.add(Button(btn_rects[2], "Check exists",
                          on_click=self._do_exists))
        panel.add(Button(btn_rects[3], "List all slots",
                          on_click=self._do_list))
        panel.add(Button(btn_rects[4], "Delete slot",
                          on_click=self._do_delete))
        panel.add(Button(btn_rects[5], "Quit",
                          on_click=self._app.stop))

        # ── Score counter ─────────────────────────────────────────────────────
        self._score_label = Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.bottom - 48,
                        panel_rect.width - 32, 28),
            f"Score to save: {self._score}",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
        )
        panel.add(self._score_label)
        panel.add(Button(
            pygame.Rect(panel_rect.x + panel_rect.width - 80,
                         panel_rect.bottom - 50, 64, 36),
            "+100",
            on_click=self._add_score,
        ))

        # ── Log panel ─────────────────────────────────────────────────────────
        log_rect = pygame.Rect(
            panel_rect.right + 40, 60,
            screen.width - panel_rect.right - 100,
            screen.height - 120,
        )
        log_panel = Panel(log_rect)
        log_panel.add(Label(
            pygame.Rect(log_rect.x + 16, log_rect.y + 12,
                        log_rect.width - 32, 28),
            "Log",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))
        self._log_label = TextBlock(
            pygame.Rect(log_rect.x + 12, log_rect.y + 52,
                        log_rect.width - 24, log_rect.height - 64),
            "",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            padding=4, line_spacing=2,
        )
        log_panel.add(self._log_label)

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(log_panel)
        self.root_widget = root

        self._log("SaveManager ready. Save dir: saves_example/")

    def _add_score(self) -> None:
        self._score += 100
        self._score_label.text = f"Score to save: {self._score}"

    def _log(self, msg: str) -> None:
        self._log_lines.append(msg)
        if len(self._log_lines) > 20:
            self._log_lines = self._log_lines[-20:]
        if self._log_label:
            self._log_label.text = "\n".join(self._log_lines)

    def _do_save(self) -> None:
        payload = {
            "score":    self._score,
            "level":    3,
            "hp":       85,
            "items":    ["sword", "potion", "key"],
        }
        self._manager.save(SAVE_SLOT, payload)
        self._log(f"✓ Saved slot '{SAVE_SLOT}' — score={self._score}")

    def _do_load(self) -> None:
        if not self._manager.exists(SAVE_SLOT):
            self._log(f"✗ Slot '{SAVE_SLOT}' does not exist"); return
        data = self._manager.load(SAVE_SLOT)
        p    = data.get("payload", {})
        self._log(f"✓ Loaded '{SAVE_SLOT}':")
        self._log(f"  score={p.get('score')}  level={p.get('level')}")
        self._log(f"  hp={p.get('hp')}  items={p.get('items')}")
        self._log(f"  saved_at={data.get('saved_at', '?')[:19]}")

    def _do_exists(self) -> None:
        exists = self._manager.exists(SAVE_SLOT)
        self._log(f"exists('{SAVE_SLOT}') → {exists}")

    def _do_list(self) -> None:
        slots = self._manager.list_slots()
        if not slots:
            self._log("No save slots found."); return
        self._log(f"All slots ({len(slots)}):")
        for s in slots:
            self._log(f"  {s.get('slot')}  @ {str(s.get('saved_at',''))[:19]}")

    def _do_delete(self) -> None:
        deleted = self._manager.delete(SAVE_SLOT)
        if deleted:
            self._log(f"✓ Deleted slot '{SAVE_SLOT}'")
        else:
            self._log(f"✗ Slot '{SAVE_SLOT}' not found — nothing deleted")

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — persistence",
        width=1280, height=720,
    ))
    app.run(PersistenceExampleScene(app))


if __name__ == "__main__":
    run()
