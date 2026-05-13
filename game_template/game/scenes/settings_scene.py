"""
game/scenes/settings_scene.py

Settings scene — pushed on top of the main menu or pause menu.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Dropdown, Label, Panel, Stack
from pygame_engine.ui.controls.checkbox import Checkbox
from pygame_engine.ui.controls.slider import Slider

from game import actions


class SettingsScene(Scene):
    """Settings overlay — pushed on top, pops on ESC or Back."""

    blocks_input_below  = True
    blocks_update_below = False
    blocks_render_below = False

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app                  = app
        self._quality_dropdown: Dropdown | None = None
        self._vol_slider:       Slider   | None = None
        self._fullscreen_cb:    Checkbox | None = None   # keep reference to sync state

    def on_enter(self) -> None:
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        # Rebuild UI at new size, preserving current fullscreen state
        self._build_ui(pygame.Rect(0, 0, width, height))

    def on_exit(self) -> None:
        pass

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self, screen: pygame.Rect) -> None:
        theme = get_theme()

        panel_rect = anchor(screen, (420, 400), "center")
        panel      = Panel(panel_rect)

        title = Label(
            pygame.Rect(panel_rect.x, panel_rect.y - 52, panel_rect.width, 40),
            "Settings",
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        )

        rows = column(
            panel_rect, count=5,
            item_size=(340, 44), spacing=10,
            padding=theme.spacing.xl,
        )

        def row_label(row: int, text: str) -> Label:
            return Label(
                pygame.Rect(rows[row].x, rows[row].y, 120, rows[row].height),
                text,
                font_size=theme.typography.sm,
                colour=theme.colours.text_secondary,
            )

        # ── Row 0: Quality ────────────────────────────────────────────────────
        panel.add(row_label(0, "Quality"))
        self._quality_dropdown = Dropdown(
            pygame.Rect(rows[0].x + 130, rows[0].y, rows[0].width - 130, rows[0].height),
            options=["Low", "Medium", "High", "Ultra"],
            selected_index=2,
            on_change=self._on_quality_change,
        )
        panel.add(self._quality_dropdown)

        # ── Row 1: Volume ─────────────────────────────────────────────────────
        panel.add(row_label(1, "Volume"))
        self._vol_slider = Slider(
            pygame.Rect(rows[1].x + 130, rows[1].y + 10, rows[1].width - 130, 24),
            value=self._app.audio.master_volume,
            on_change=lambda v: setattr(self._app.audio, "master_volume", v),
        )
        panel.add(self._vol_slider)

        # ── Row 2: Fullscreen ─────────────────────────────────────────────────
        panel.add(row_label(2, "Display"))

        # Read the ACTUAL current fullscreen state from pygame so the checkbox
        # always reflects reality (e.g. after on_resize rebuilds the UI).
        is_fullscreen = self._is_fullscreen()

        self._fullscreen_cb = Checkbox(
            pygame.Rect(rows[2].x + 130, rows[2].y, 200, rows[2].height),
            label="Fullscreen",
            checked=is_fullscreen,
            on_change=self._on_fullscreen_change,
        )
        panel.add(self._fullscreen_cb)

        # ── Row 3: Show FPS ───────────────────────────────────────────────────
        panel.add(row_label(3, ""))
        panel.add(Checkbox(
            pygame.Rect(rows[3].x + 130, rows[3].y, 200, rows[3].height),
            label="Show FPS",
            on_change=self._on_show_fps_change,
        ))

        # ── Row 4: Back ───────────────────────────────────────────────────────
        panel.add(Button(rows[4], "Back", on_click=self._go_back))

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        self.root_widget = root

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
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
        if self._quality_dropdown is not None:
            self._quality_dropdown.overlay_render(surface)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_quality_change(self, value: str, index: int) -> None:
        pass   # wire up quality settings here

    def _on_fullscreen_change(self, value: bool) -> None:
        self._app.set_fullscreen(value)
        # After set_fullscreen the display is recreated. on_resize fires and
        # rebuilds the UI with a fresh checkbox that reads is_fullscreen()
        # directly, so the visual state will always be correct.

    def _on_show_fps_change(self, value: bool) -> None:
        from pygame_engine.state.runtime_flags import flags
        flags.show_overlay = value

    def _go_back(self) -> None:
        self._app.scene_manager.pop_with(
            SlideTransition(duration=0.3, direction="right"),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_fullscreen(self) -> bool:
        """Return True if the display is currently in fullscreen mode."""
        surf = pygame.display.get_surface()
        if surf is None:
            return False
        return bool(surf.get_flags() & pygame.FULLSCREEN)
