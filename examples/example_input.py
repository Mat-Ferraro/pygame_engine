"""
Demonstrates key remapping and controller support.

What this example shows:
- Live key remapping with an Apply/Cancel workflow
- Current keyboard binding displayed per action
- Controller detection and button display
- Bindings reset to defaults
- Pending changes shown before applying

Controls:
    Click an action row — select it for remapping
    Press a key        — set the pending binding
    Apply              — commit all pending changes
    Discard            — throw away pending changes
    R                  — reset to defaults
    ESC                — quit (only when no pending changes)

Run from the repo root:
    python -m examples.example_input
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.input.bindings import controller_button_name, key_name
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack

REMAPPABLE = [
    (actions.CONFIRM,    "Confirm"),
    (actions.CANCEL,     "Cancel / Back"),
    (actions.NAV_UP,     "Move Up"),
    (actions.NAV_DOWN,   "Move Down"),
    (actions.NAV_LEFT,   "Move Left"),
    (actions.NAV_RIGHT,  "Move Right"),
    (actions.PAUSE,      "Pause"),
]

ROW_H   = 40
ROW_GAP = 4
COL_ACTION  = 0
COL_KB      = 220
COL_PENDING = 410
COL_CTRL    = 580


class InputExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app              = app
        self._selected_index:  int = -1          # row being remapped
        self._pending:         dict[str, int] = {}  # action → new key (not yet applied)
        self._kb_labels:       list[Label] = []
        self._pending_labels:  list[Label] = []
        self._ctrl_labels:     list[Label] = []
        self._row_rects:       list[pygame.Rect] = []
        self._status:          Label | None = None
        self._apply_btn:       Button | None = None
        self._discard_btn:     Button | None = None

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()
        inp   = self._app.input_manager

        TABLE_W  = 820
        HEADER_H = 28
        PADDING  = 20
        TABLE_H  = (PADDING + HEADER_H
                    + len(REMAPPABLE) * (ROW_H + ROW_GAP)
                    + PADDING)

        panel_rect = anchor(screen, (TABLE_W, TABLE_H), "center", offset=(0, 10))
        panel      = Panel(panel_rect)

        # ── Column headers ─────────────────────────────────────────────────────
        hx = panel_rect.x + 16
        hy = panel_rect.y + PADDING
        for x_off, header in [
            (COL_ACTION,  "Action"),
            (COL_KB,      "Current Key"),
            (COL_PENDING, "Pending"),
            (COL_CTRL,    "Controller"),
        ]:
            panel.add(Label(
                pygame.Rect(hx + x_off, hy, 180, HEADER_H),
                header,
                font_size=theme.typography.sm,
                colour=theme.colours.text_secondary,
            ))

        # ── Rows ───────────────────────────────────────────────────────────────
        table_top = panel_rect.y + PADDING + HEADER_H + 4
        self._row_rects      = []
        self._kb_labels      = []
        self._pending_labels = []
        self._ctrl_labels    = []

        for i, (action, label) in enumerate(REMAPPABLE):
            ry = table_top + i * (ROW_H + ROW_GAP)
            self._row_rects.append(
                pygame.Rect(panel_rect.x + 8, ry,
                            panel_rect.width - 16, ROW_H))

            panel.add(Label(
                pygame.Rect(hx + COL_ACTION, ry, 190, ROW_H),
                label, font_size=theme.typography.sm, colour=theme.colours.text,
            ))

            key    = inp.get_key_for_action(action)
            kb_lbl = Label(
                pygame.Rect(hx + COL_KB, ry, 170, ROW_H),
                key_name(key) if key is not None else "—",
                font_size=theme.typography.sm, colour=theme.colours.text,
            )
            panel.add(kb_lbl)
            self._kb_labels.append(kb_lbl)

            # Pending column — shows what will be applied
            pending_key = self._pending.get(action)
            pnd_lbl = Label(
                pygame.Rect(hx + COL_PENDING, ry, 160, ROW_H),
                key_name(pending_key) if pending_key is not None else "",
                font_size=theme.typography.sm,
                colour=(100, 220, 120),   # green = pending change
            )
            panel.add(pnd_lbl)
            self._pending_labels.append(pnd_lbl)

            btn    = inp.get_button_for_action(action)
            ct_lbl = Label(
                pygame.Rect(hx + COL_CTRL, ry, 220, ROW_H),
                controller_button_name(btn) if btn is not None else "—",
                font_size=theme.typography.sm,
                colour=theme.colours.text_secondary,
            )
            panel.add(ct_lbl)
            self._ctrl_labels.append(ct_lbl)

        # ── Controller status ──────────────────────────────────────────────────
        ctrl_rect  = anchor(screen, (280, 80), "top_right", margin=40)
        ctrl_panel = Panel(ctrl_rect)
        ctrl_count = inp.controller_count
        ctrl_panel.add(Label(
            pygame.Rect(ctrl_rect.x + 12, ctrl_rect.y + 12,
                        ctrl_rect.width - 24, 24),
            f"Controllers: {ctrl_count} connected",
            font_size=theme.typography.sm,
            colour=(100, 220, 100) if ctrl_count else theme.colours.text_secondary,
        ))

        # ── Action buttons ─────────────────────────────────────────────────────
        btn_y = panel_rect.bottom + 12
        self._apply_btn = Button(
            pygame.Rect(panel_rect.right - 340, btn_y, 160, 38),
            "Apply Changes",
            on_click=self._apply,
        )
        self._discard_btn = Button(
            pygame.Rect(panel_rect.right - 170, btn_y, 160, 38),
            "Discard",
            on_click=self._discard,
        )
        reset_btn = Button(
            anchor(screen, (160, 38), "bottom_left", margin=60),
            "Reset Defaults",
            on_click=self._reset_defaults,
        )

        self._status = Label(
            anchor(screen, (700, 22), "bottom", margin=18),
            "Click a row to select  •  press a key  •  Apply to confirm  •  ESC = quit",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        )

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(ctrl_panel)
        root.add(self._apply_btn)
        root.add(self._discard_btn)
        root.add(reset_btn)
        root.add(Label(
            anchor(screen, (500, 36), "top", margin=20),
            "Input & Controller Demo",
            font_size=theme.typography.xl,
            colour=theme.colours.text, align="center",
        ))
        root.add(self._status)
        self.root_widget = root
        self._update_button_visibility()

    # ── Pending workflow ──────────────────────────────────────────────────────

    def _apply(self) -> None:
        """Commit all pending bindings to the InputManager."""
        inp = self._app.input_manager
        for action, key in self._pending.items():
            inp.remap(action, key)
        self._pending.clear()
        self._selected_index = -1
        self._refresh_all_labels()
        self._set_status("Changes applied.")
        self._update_button_visibility()

    def _discard(self) -> None:
        """Throw away all pending changes."""
        self._pending.clear()
        self._selected_index = -1
        self._refresh_all_labels()
        self._set_status("Changes discarded.")
        self._update_button_visibility()

    def _reset_defaults(self) -> None:
        self._pending.clear()
        self._selected_index = -1
        self._app.input_manager.reset_to_defaults()
        self._build_ui(self._app.screen_rect)

    def _update_button_visibility(self) -> None:
        has_pending = bool(self._pending)
        if self._apply_btn:   self._apply_btn.enabled   = has_pending
        if self._discard_btn: self._discard_btn.enabled = has_pending

    # ── Label refresh ─────────────────────────────────────────────────────────

    def _refresh_all_labels(self) -> None:
        inp = self._app.input_manager
        for i, (action, _) in enumerate(REMAPPABLE):
            if i < len(self._kb_labels):
                key = inp.get_key_for_action(action)
                self._kb_labels[i].text = key_name(key) if key is not None else "—"
            if i < len(self._pending_labels):
                pk = self._pending.get(action)
                self._pending_labels[i].text = key_name(pk) if pk is not None else ""

    def _set_status(self, msg: str) -> None:
        if self._status:
            self._status.text = msg

    # ── Events ────────────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager

        # Key press — set pending binding for selected row
        if event.type == pygame.KEYDOWN and self._selected_index >= 0:
            action = REMAPPABLE[self._selected_index][0]
            self._pending[action] = event.key
            self._pending_labels[self._selected_index].text = key_name(event.key)
            self._selected_index = -1
            self._update_button_visibility()
            self._set_status(
                f"Pending: {key_name(event.key)} → click Apply to confirm"
                "   •   ESC = quit"
            )
            return True

        # Reset shortcut
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._reset_defaults(); return True

        # Row click — select for remapping
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, row_rect in enumerate(self._row_rects):
                if row_rect.collidepoint(event.pos):
                    self._selected_index = i
                    name = REMAPPABLE[i][1]
                    self._set_status(f"Selected '{name}' — press any key to set pending binding")
                    return True

        # ESC quits only when no pending changes and not selecting
        if (self._selected_index < 0
                and not self._pending
                and inp.was_action_pressed(actions.CANCEL)):
            self._app.stop(); return True

        # ESC cancels current row selection
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._selected_index >= 0:
                self._selected_index = -1
                self._set_status(
                    "Click a row to select  •  Apply to confirm  •  ESC = quit"
                )
                return True

        return False

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)

        theme = get_theme()
        mouse = pygame.mouse.get_pos()
        for i, row_rect in enumerate(self._row_rects):
            is_selected = (i == self._selected_index)
            is_hovered  = row_rect.collidepoint(mouse) and not is_selected
            has_pending = REMAPPABLE[i][0] in self._pending

            if is_selected:
                col = (*theme.button.pressed.bg, 220)
            elif has_pending:
                col = (40, 100, 60, 160)   # green tint for pending rows
            elif is_hovered:
                col = (*theme.button.normal.bg, 100)
            else:
                col = (*theme.colours.bg_raised, 140)

            hl = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            hl.fill(col)
            surface.blit(hl, row_rect.topleft)
            pygame.draw.rect(surface, theme.colours.border, row_rect,
                             width=1, border_radius=4)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — input & controller",
        width=1280, height=720,
        resizable=True,
    ))
    app.run(InputExampleScene(app))


if __name__ == "__main__":
    run()
