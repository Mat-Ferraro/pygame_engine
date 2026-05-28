"""
What this example shows:
- F1 toggles the debug overlay (FPS, scene, stack, active flags)
- F3 toggles the debug console log panel
- RuntimeFlags: what each flag actually does
- debug_log log() / warn() / error() / get_entries() / clear()

Flag reference:
    show_overlay  — shows the top-left debug info panel (F1)
    show_console  — shows the bottom debug console (F3)
    show_fps      — shown inside the overlay when overlay is active
    show_rects    — draws coloured outlines around all widget rects
    debug         — master switch (no direct visual effect by itself)

Controls:
    F1  — toggle show_overlay
    F3  — toggle show_console
    L   — write info log entry
    W   — write warning entry
    E   — write error entry
    C   — clear log
    D   — toggle debug master flag
    T   — toggle show_rects (see widget outlines)
    R   — reset all flags

Run from the repo root:
    python -m examples.example_debug
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.devtools.debug_log import clear as log_clear
from pygame_engine.devtools.debug_log import error as log_error
from pygame_engine.devtools.debug_log import get_entries
from pygame_engine.devtools.debug_log import log as log_info
from pygame_engine.devtools.debug_log import warn as log_warn
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.state.runtime_flags import flags
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.ui.text.text_block import TextBlock

_COUNTER = 0


class DebugExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app         = app
        self._log_block:  TextBlock | None = None
        self._flag_block: TextBlock | None = None

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)
        log_info("Debug example started", tag="example")
        self._refresh()

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()

        # ── Left panel: controls ──────────────────────────────────────────────
        # Fixed height — enough for 8 buttons + flag text block
        panel_rect = pygame.Rect(60, 60, 320, 620)
        panel      = Panel(panel_rect)

        panel.add(Label(
            pygame.Rect(panel_rect.x + 16, panel_rect.y + 12,
                        panel_rect.width - 32, 28),
            "Debug Tools",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))

        btn_rects = column(panel_rect, count=8,
                           item_size=(260, 40), spacing=6,
                           padding=theme.spacing.xl + 16)

        panel.add(Button(btn_rects[0], "F1 — toggle show_overlay",
                          on_click=lambda: (flags.toggle("show_overlay"), self._refresh())))
        panel.add(Button(btn_rects[1], "F3 — toggle show_console",
                          on_click=lambda: (flags.toggle("show_console"), self._refresh())))
        panel.add(Button(btn_rects[2], "D — toggle debug",
                          on_click=lambda: (flags.toggle("debug"), self._refresh())))
        panel.add(Button(btn_rects[3], "T — toggle show_rects",
                          on_click=lambda: (flags.toggle("show_rects"), self._refresh())))
        panel.add(Button(btn_rects[4], "L — log info",
                          on_click=self._write_log))
        panel.add(Button(btn_rects[5], "W — log warning",
                          on_click=self._write_warn))
        panel.add(Button(btn_rects[6], "E — log error",
                          on_click=self._write_error))
        panel.add(Button(btn_rects[7], "C — clear log",
                          on_click=self._clear_log))

        # Flag state display — sits below buttons with enough room
        flag_y = btn_rects[-1].bottom + 16
        self._flag_block = TextBlock(
            pygame.Rect(panel_rect.x + 16, flag_y,
                        panel_rect.width - 32, panel_rect.bottom - flag_y - 12),
            self._flag_text(),
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            padding=0,
        )
        panel.add(self._flag_block)

        # ── Right panel: log viewer ───────────────────────────────────────────
        log_rect = pygame.Rect(
            panel_rect.right + 24, 60,
            screen.width - panel_rect.right - 84,
            screen.height - 120,
        )
        log_panel = Panel(log_rect)
        log_panel.add(Label(
            pygame.Rect(log_rect.x + 16, log_rect.y + 12,
                        log_rect.width - 32, 28),
            "debug_log entries",
            font_size=theme.typography.lg, colour=theme.colours.text,
        ))
        self._log_block = TextBlock(
            pygame.Rect(log_rect.x + 12, log_rect.y + 52,
                        log_rect.width - 24, log_rect.height - 64),
            self._format_log(),
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            padding=4, line_spacing=2,
        )
        log_panel.add(self._log_block)

        # ── Hint ──────────────────────────────────────────────────────────────
        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(log_panel)
        root.add(Label(
            anchor(screen, (760, 22), "bottom", margin=14),
            "F1=overlay  F3=console  L/W/E=log  C=clear  "
            "D=debug  T=show_rects  R=reset  ESC=quit",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        ))
        self.root_widget = root

    def _flag_text(self) -> str:
        d = flags.as_dict()
        lines = ["Active flags:"]
        for k, v in sorted(d.items()):
            marker = "■" if v else "□"
            lines.append(f"  {marker} {k}: {v}")
        return "\n".join(lines)

    def _format_log(self) -> str:
        entries = get_entries(limit=30)
        if not entries:
            return "(no log entries yet — press L, W, or E)"
        return "\n".join(
            f"[{e.level.upper()[:4]}] [{e.tag}] {e.message}"
            for e in entries
        )

    def _write_log(self) -> None:
        global _COUNTER
        _COUNTER += 1
        log_info(f"Info message #{_COUNTER}", tag="example")
        self._refresh()

    def _write_warn(self) -> None:
        log_warn("Warning: something unusual happened", tag="example")
        self._refresh()

    def _write_error(self) -> None:
        log_error("Error logged (not raised)", tag="example")
        self._refresh()

    def _clear_log(self) -> None:
        log_clear()
        self._refresh()

    def _refresh(self) -> None:
        if self._log_block:
            self._log_block.text  = self._format_log()
        if self._flag_block:
            self._flag_block.text = self._flag_text()

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k == pygame.K_l: self._write_log();                          return True
            if k == pygame.K_w: self._write_warn();                          return True
            if k == pygame.K_e: self._write_error();                         return True
            if k == pygame.K_c: self._clear_log();                           return True
            if k == pygame.K_d: flags.toggle("debug");   self._refresh();    return True
            if k == pygame.K_t: flags.toggle("show_rects"); self._refresh(); return True
            if k == pygame.K_r: flags.reset();           self._refresh();    return True
        return False

    def update(self, dt: float) -> None:
        self._refresh()
        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — debug tools",
        width=1280, height=720,
        resizable=True,
        mode="development",
    ))
    app.run(DebugExampleScene(app))


if __name__ == "__main__":
    run()