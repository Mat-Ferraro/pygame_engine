"""
Demonstrates GlobalFocusManager — application-wide keyboard focus.

What this example shows:
- app.focus.set_candidates(widgets) — register focusable widgets
- Tab / Shift+Tab navigation via next_focus() / prev_focus()
- tab_index ordering — explicitly ordered widgets come first
- focus_trap — a modal panel that traps focus inside itself
- focus_ring — the 2px ring drawn automatically by Application
- ui.focus.changed bus event — react to focus changes
- widget_id — identify focused widget by name in the status bar

Two panels are shown:
  Left panel  — widgets with explicit tab_index ordering
  Right panel — auto-ordering (document order) + focus trap demo

Controls:
    Tab           — focus next widget
    Shift+Tab     — focus previous widget
    Enter / Space — activate focused button
    M             — open modal dialog (focus trap demo)
    ESC           — close modal / quit

Run from the repo root:
    python -m examples.example_focus
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.events.event_bus import bus
from pygame_engine.layout import anchor, column, row
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.ui.base.widget import Widget
from pygame_engine.ui.controls.input_field import InputField


class FocusScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app     = app
        self._status: Label | None = None
        self._modal: Panel | None = None
        self._modal_visible = False
        self._all_focusable: list[Widget] = []

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()
        fm     = self._app.focus

        candidates: list[Widget] = []

        # ── Left panel: tab_index ordering ───────────────────────────────────
        lp_rect = pygame.Rect(screen.x + 40, screen.y + 60,
                              480, screen.height - 120)
        lp = Panel(lp_rect)
        lp.add(Label(
            pygame.Rect(lp_rect.x + 16, lp_rect.y + 10, lp_rect.width - 32, 28),
            "tab_index ordering (2 → 0 → 1)",
            font_size=theme.typography.md, colour=theme.colours.text,
        ))

        # Intentionally add in "wrong" order — tab_index will reorder them
        btn_rects = column(
            pygame.Rect(lp_rect.x, lp_rect.y + 50,
                        lp_rect.width, 260),
            count=3, item_size=(lp_rect.width - 32, 48), spacing=12,
            padding=theme.spacing.lg,
        )

        btn_b = Button(btn_rects[0], "Button B  (tab_index=2)",
                       on_click=lambda: self._set_status("Button B clicked"))
        btn_b.widget_id  = "btn_b"
        btn_b.tab_index  = 2

        btn_a = Button(btn_rects[1], "Button A  (tab_index=0)",
                       on_click=lambda: self._set_status("Button A clicked"))
        btn_a.widget_id  = "btn_a"
        btn_a.tab_index  = 0

        btn_c = Button(btn_rects[2], "Button C  (tab_index=1)",
                       on_click=lambda: self._set_status("Button C clicked"))
        btn_c.widget_id  = "btn_c"
        btn_c.tab_index  = 1

        lp.add(btn_b)
        lp.add(btn_a)
        lp.add(btn_c)
        candidates.extend([btn_b, btn_a, btn_c])

        lp.add(Label(
            pygame.Rect(lp_rect.x + 16, btn_rects[2].bottom + 16,
                        lp_rect.width - 32, 60),
            "Tab order will be: A → C → B\n(sorted by tab_index value)",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
        ))

        # ── Right panel: document order + input fields ────────────────────────
        rp_rect = pygame.Rect(screen.centerx + 20, screen.y + 60,
                              480, screen.height - 120)
        rp = Panel(rp_rect)
        rp.add(Label(
            pygame.Rect(rp_rect.x + 16, rp_rect.y + 10, rp_rect.width - 32, 28),
            "Document order (no tab_index)",
            font_size=theme.typography.md, colour=theme.colours.text,
        ))

        field_rects = column(
            pygame.Rect(rp_rect.x, rp_rect.y + 50, rp_rect.width, 220),
            count=3, item_size=(rp_rect.width - 32, 44), spacing=12,
            padding=theme.spacing.lg,
        )

        for i, rect in enumerate(field_rects):
            f = InputField(rect, placeholder=f"Field {i + 1}")
            f.widget_id = f"field_{i+1}"
            rp.add(f)
            candidates.append(f)

        modal_btn = Button(
            pygame.Rect(rp_rect.x + 16, field_rects[-1].bottom + 20,
                        rp_rect.width - 32, 44),
            "Open modal dialog (M)",
            on_click=self._open_modal,
        )
        modal_btn.widget_id = "modal_btn"
        rp.add(modal_btn)
        candidates.append(modal_btn)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status = Label(
            anchor(screen, (screen.width - 40, 36), "bottom", margin=16),
            "Tab to move focus   |   Enter/Space to activate   |   M for modal",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            align="center",
        )

        # ── Modal panel (focus trap) ──────────────────────────────────────────
        m_rect = anchor(screen, (400, 220), "center")
        self._modal = Panel(m_rect)
        self._modal.visible = False
        self._modal.focus_trap = True

        self._modal.add(Label(
            pygame.Rect(m_rect.x + 16, m_rect.y + 16, m_rect.width - 32, 28),
            "Modal Dialog (focus trapped)",
            font_size=theme.typography.md, colour=theme.colours.text,
        ))
        self._modal.add(Label(
            pygame.Rect(m_rect.x + 16, m_rect.y + 52, m_rect.width - 32, 40),
            "Tab stays inside this dialog.\nPress Confirm or Cancel to close.",
            font_size=theme.typography.sm, colour=theme.colours.text_secondary,
        ))

        modal_btns = row(
            pygame.Rect(m_rect.x, m_rect.y + 120, m_rect.width, 64),
            count=2, item_size=(160, 44), spacing=16, padding=theme.spacing.lg,
        )
        m_confirm = Button(modal_btns[0], "Confirm",
                           on_click=self._close_modal)
        m_cancel  = Button(modal_btns[1], "Cancel",
                           on_click=self._close_modal)
        m_confirm.widget_id = "modal_confirm"
        m_cancel.widget_id  = "modal_cancel"
        self._modal.add(m_confirm)
        self._modal.add(m_cancel)
        self._modal_buttons = [m_confirm, m_cancel]

        # ── Wire candidates into GlobalFocusManager ───────────────────────────
        self._all_focusable = candidates
        fm.set_candidates(candidates)
        fm.next_focus()   # focus first widget on enter

        # React to focus changes via event bus
        self.subscriptions.on(
            # EventBus doesn't use Observable, wire manually
        )
        bus.on("ui.focus.changed", self._on_focus_changed)

        # ── Root widget ───────────────────────────────────────────────────────
        root = Stack(pygame.Rect(screen))
        root.add(lp)
        root.add(rp)
        root.add(self._status)
        root.add(self._modal)
        self.root_widget = root

    def on_exit(self) -> None:
        super().on_exit()
        bus.off("ui.focus.changed", self._on_focus_changed)

    def _on_focus_changed(self, widget: Widget | None = None) -> None:
        if widget is None:
            self._set_status("Focus cleared")
        else:
            wid = getattr(widget, "widget_id", None) or type(widget).__name__
            self._set_status(f"Focused: {wid}")

    def _set_status(self, msg: str) -> None:
        if self._status:
            self._status.text = msg

    def _open_modal(self) -> None:
        if self._modal:
            self._modal.visible = True
            self._modal_visible = True
            self._app.focus.set_candidates(self._modal_buttons)
            self._app.focus.next_focus()

    def _close_modal(self) -> None:
        if self._modal:
            self._modal.visible = False
            self._modal_visible = False
            self._app.focus.set_candidates(self._all_focusable)
            self._app.focus.next_focus()

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        fm = self._app.focus
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if event.key == pygame.K_TAB:
                if mods & pygame.KMOD_SHIFT:
                    fm.prev_focus()
                else:
                    fm.next_focus()
                return True
            if event.key == pygame.K_m and not self._modal_visible:
                self._open_modal(); return True
            if event.key == pygame.K_ESCAPE:
                if self._modal_visible:
                    self._close_modal()
                else:
                    self._app.stop()
                return True
        return False

    def render(self, surface: pygame.Surface, ctx=None) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface, ctx)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — GlobalFocusManager",
        width=1280, height=720, resizable=True,
    ))
    app.run(FocusScene(app))


if __name__ == "__main__":
    run()
