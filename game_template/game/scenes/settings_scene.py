"""
game/scenes/settings_scene.py

Settings scene — pushed on top of the main menu or pause menu.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.input.bindings import key_name
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Dropdown, Label, Panel, Stack
from pygame_engine.ui.controls.checkbox import Checkbox
from pygame_engine.ui.controls.slider import Slider

from game import actions
from game.locale import t


class SettingsScene(Scene):
    """
    Settings overlay — two tabs: Video/Audio and Controls.

    Video/Audio tab:
    - Quality dropdown
    - Volume slider
    - Fullscreen checkbox
    - Show FPS checkbox

    Controls tab:
    - Live key remapping (click row, press new key)
    - Reset to defaults
    - Bindings saved to 'settings' slot on exit
    """

    blocks_input_below  = True
    blocks_update_below = False
    blocks_render_below = False

    REMAPPABLE = [
        (actions.CONFIRM,    "Confirm"),
        (actions.CANCEL,     "Cancel / Back"),
        (actions.NAV_UP,     "Move Up"),
        (actions.NAV_DOWN,   "Move Down"),
        (actions.NAV_LEFT,   "Move Left"),
        (actions.NAV_RIGHT,  "Move Right"),
        (actions.PAUSE,      "Pause"),
    ]

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app              = app
        self._quality_dropdown: Dropdown | None = None
        self._vol_slider:       Slider   | None = None
        self._fullscreen_cb:    Checkbox | None = None
        self._active_tab       = "video"
        self._awaiting_remap:  str | None = None
        self._remap_labels:    list[Label] = []
        self._status_label:    Label | None = None

    def on_enter(self) -> None:
        self._load_bindings()
        self._build_ui(self._app.screen_rect)

    def on_exit(self) -> None:
        self._save_bindings()

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_bindings(self) -> None:
        try:
            from pygame_engine.persistence import SaveManager
            from pathlib import Path
            sm = SaveManager(save_dir=Path("saves"))
            sm.save("settings", {
                "bindings": self._app.input_manager.bindings_to_dict(),
            })
        except Exception:
            pass   # persistence unavailable — silent

    def _load_bindings(self) -> None:
        try:
            from pygame_engine.persistence import SaveManager
            from pathlib import Path
            sm = SaveManager(save_dir=Path("saves"))
            if sm.exists("settings"):
                data = sm.load("settings")
                if "bindings" in data.get("payload", {}):
                    self._app.input_manager.bindings_from_dict(
                        data["payload"]["bindings"]
                    )
        except Exception:
            pass

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()
        root  = Stack(pygame.Rect(screen))

        title = Label(
            anchor(screen, (400, 40), "top", margin=60),
            t("settings.title"),
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        )

        # Tab buttons
        tab_y   = 112
        tab_w   = 160
        tab_gap = 8
        tx      = screen.centerx - tab_w - tab_gap // 2

        video_btn = Button(
            pygame.Rect(tx, tab_y, tab_w, 38),
            "Video & Audio",
            on_click=lambda: self._switch_tab("video"),
        )
        ctrl_btn = Button(
            pygame.Rect(tx + tab_w + tab_gap, tab_y, tab_w, 38),
            "Controls",
            on_click=lambda: self._switch_tab("controls"),
        )

        self._status_label = Label(
            anchor(screen, (600, 24), "bottom", margin=14),
            "",
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary,
            align="center",
        )

        root.add(title)
        root.add(video_btn)
        root.add(ctrl_btn)
        root.add(self._status_label)

        if self._active_tab == "video":
            root.add(self._build_video_tab(screen))
        else:
            root.add(self._build_controls_tab(screen))

        self.root_widget = root

    def _build_video_tab(self, screen: pygame.Rect) -> Panel:
        theme      = get_theme()
        panel_rect = anchor(screen, (420, 300), "center", offset=(0, 30))
        panel      = Panel(panel_rect)

        rows = column(panel_rect, count=4,
                      item_size=(340, 44), spacing=10,
                      padding=get_theme().spacing.xl)

        def row_label(row, key):
            return Label(pygame.Rect(rows[row].x, rows[row].y, 130, rows[row].height),
                         t(key), font_size=theme.typography.sm,
                         colour=theme.colours.text_secondary)

        panel.add(row_label(0, "settings.quality"))
        self._quality_dropdown = Dropdown(
            pygame.Rect(rows[0].x+140, rows[0].y, rows[0].width-140, rows[0].height),
            options=["Low", "Medium", "High", "Ultra"],
            selected_index=2, on_change=self._on_quality_change,
        )
        panel.add(self._quality_dropdown)

        panel.add(row_label(1, "settings.volume"))
        self._vol_slider = Slider(
            pygame.Rect(rows[1].x+140, rows[1].y+10, rows[1].width-140, 24),
            value=self._app.audio.master_volume,
            on_change=lambda v: setattr(self._app.audio, "master_volume", v),
        )
        panel.add(self._vol_slider)

        panel.add(row_label(2, "settings.display"))
        self._fullscreen_cb = Checkbox(
            pygame.Rect(rows[2].x+140, rows[2].y, 200, rows[2].height),
            label=t("settings.fullscreen"), checked=self._is_fullscreen(),
            on_change=self._on_fullscreen_change,
        )
        panel.add(self._fullscreen_cb)

        panel.add(row_label(3, "settings.display"))
        panel.add(Checkbox(
            pygame.Rect(rows[3].x+140, rows[3].y, 200, rows[3].height),
            label=t("settings.show_fps"), on_change=self._on_show_fps_change,
        ))

        return panel

    def _build_controls_tab(self, screen: pygame.Rect) -> Panel:
        theme      = get_theme()
        panel_rect = anchor(screen, (560, 380), "center", offset=(0, 30))
        panel      = Panel(panel_rect)
        inp        = self._app.input_manager

        self._remap_labels = []
        rows = column(panel_rect, count=len(self.REMAPPABLE),
                      item_size=(panel_rect.width-40, 38),
                      spacing=4, padding=theme.spacing.xl)

        for i, (action, label) in enumerate(self.REMAPPABLE):
            r = rows[i]
            panel.add(Label(pygame.Rect(r.x+10, r.y, 180, r.height),
                            label, font_size=theme.typography.sm,
                            colour=theme.colours.text))
            key     = inp.get_key_for_action(action)
            kb_lbl  = Label(pygame.Rect(r.x+200, r.y, 160, r.height),
                            key_name(key) if key else "—",
                            font_size=theme.typography.sm,
                            colour=theme.colours.text)
            panel.add(kb_lbl)
            self._remap_labels.append(kb_lbl)

            def make_btn(act=action):
                b = Button(pygame.Rect(r.x, r.y, 360, r.height), "",
                           on_click=lambda a=act: self._start_remap(a))
                return b
            panel.add(make_btn())

        reset_rect = pygame.Rect(
            panel_rect.x + panel_rect.width - 160,
            panel_rect.bottom + 10, 150, 36,
        )
        panel.add(Button(reset_rect, "Reset Defaults",
                         on_click=self._reset_bindings))

        return panel

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, tab: str) -> None:
        self._active_tab = tab
        self._awaiting_remap = None
        self._build_ui(self._app.screen_rect)

    # ── Remap ─────────────────────────────────────────────────────────────────

    def _start_remap(self, action: str) -> None:
        self._awaiting_remap = action
        if self._status_label:
            self._status_label.text = f"Press any key to bind to '{action}' ..."

    def _reset_bindings(self) -> None:
        self._app.input_manager.reset_to_defaults()
        self._awaiting_remap = None
        self._build_ui(self._app.screen_rect)

    def _refresh_remap_labels(self) -> None:
        inp = self._app.input_manager
        for i, (action, _) in enumerate(self.REMAPPABLE):
            if i < len(self._remap_labels):
                key = inp.get_key_for_action(action)
                self._remap_labels[i].text = key_name(key) if key else "—"

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._awaiting_remap:
            if event.type == pygame.KEYDOWN:
                self._app.input_manager.remap(self._awaiting_remap, event.key)
                self._awaiting_remap = None
                self._refresh_remap_labels()
                if self._status_label:
                    self._status_label.text = "Binding updated."
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._awaiting_remap = None
                return True

        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._go_back()
            return True
        return False

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))
        super().render(surface)

    def overlay_render(self, surface: pygame.Surface) -> None:
        if self._quality_dropdown is not None and self._active_tab == "video":
            self._quality_dropdown.overlay_render(surface)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_quality_change(self, value: str, index: int) -> None:
        pass

    def _on_fullscreen_change(self, value: bool) -> None:
        self._app.set_fullscreen(value)

    def _on_show_fps_change(self, value: bool) -> None:
        from pygame_engine.state.runtime_flags import flags
        flags.show_overlay = value

    def _go_back(self) -> None:
        self._app.scene_manager.pop_with(
            SlideTransition(duration=0.3, direction="right"),
        )

    def _is_fullscreen(self) -> bool:
        surf = pygame.display.get_surface()
        if surf is None:
            return False
        return bool(surf.get_flags() & pygame.FULLSCREEN)
