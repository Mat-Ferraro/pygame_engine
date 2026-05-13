"""
game/scenes/settings_scene.py

Settings scene.

Pushed on top of the main menu (or pause menu). Slides in, pops back
on Back or ESC.

Demonstrates:
- Dropdown with overlay_render() via the scene's overlay_render pass
- ProgressBar as a volume display
- Button for a boolean toggle (fullscreen)
- The correct pattern for floating UI in a scene

Extend with additional controls as needed.
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene, SlideTransition
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Dropdown, Label, Panel, ProgressBar, Stack

from game import actions


class SettingsScene(Scene):
    """
    Settings overlay — pushed on top, pops back on ESC or Back.

    Demonstrates overlay_render for Dropdown z-ordering.
    """

    # Does not block rendering below — scene beneath stays visible
    blocks_input_below  = True
    blocks_update_below = False
    blocks_render_below = False

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._quality_dropdown: Dropdown | None = None
        self._volume_bar:       ProgressBar | None = None

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)
        theme = get_theme()

        # ── Panel ─────────────────────────────────────────────────────────────
        panel_rect = anchor(screen, (380, 360), "center")
        panel = Panel(panel_rect)

        title_rect = pygame.Rect(panel_rect.x,
                                 panel_rect.y - 52,
                                 panel_rect.width, 40)
        title = Label(title_rect, "Settings",
                      font_size=theme.typography.xl,
                      colour=theme.colours.text,
                      align="center")

        # ── Controls ──────────────────────────────────────────────────────────
        rows = column(
            panel_rect, count=4,
            item_size=(300, 44), spacing=12,
            padding=theme.spacing.xl,
        )

        # Row 0: quality label + dropdown
        quality_label = Label(
            pygame.Rect(rows[0].x, rows[0].y, 120, rows[0].height),
            "Quality",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
        )
        quality_rect = pygame.Rect(
            rows[0].x + 130, rows[0].y,
            rows[0].width - 130, rows[0].height,
        )
        self._quality_dropdown = Dropdown(
            quality_rect,
            options=["Low", "Medium", "High", "Ultra"],
            selected_index=2,
            on_change=self._on_quality_change,
        )

        # Row 1: volume label + bar
        volume_label = Label(
            pygame.Rect(rows[1].x, rows[1].y, 120, rows[1].height),
            "Volume",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
        )
        self._volume_bar = ProgressBar(
            pygame.Rect(rows[1].x + 130, rows[1].y + 14,
                        rows[1].width - 130, 16),
            value=self._app.audio.master_volume,
        )

        # Row 2: volume buttons
        vol_down = Button(
            pygame.Rect(rows[2].x + 130, rows[2].y, 60, rows[2].height),
            "−", on_click=self._volume_down,
        )
        vol_up = Button(
            pygame.Rect(rows[2].x + 200, rows[2].y, 60, rows[2].height),
            "+", on_click=self._volume_up,
        )

        # Row 3: back button
        btn_back = Button(rows[3], "Back", on_click=self._go_back)

        panel.add(quality_label)
        panel.add(self._quality_dropdown)
        panel.add(volume_label)
        panel.add(self._volume_bar)
        panel.add(vol_down)
        panel.add(vol_up)
        panel.add(btn_back)

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        self.root_widget = root

    def on_exit(self) -> None:
        pass

    # ── Event handling ────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._go_back()
            return True
        return False

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay over the scene below
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))
        super().render(surface)   # renders widget tree + calls overlay_render

    def overlay_render(self, surface: pygame.Surface) -> None:
        """
        Render the quality dropdown's open list on top of everything.

        Called automatically by Scene.render() after the main widget tree.
        Any Dropdown or floating Tooltip in this scene is rendered here.
        """
        if self._quality_dropdown is not None:
            self._quality_dropdown.overlay_render(surface)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_quality_change(self, value: str, index: int) -> None:
        """Apply quality setting when dropdown selection changes."""
        # Example: quality_map = {"Low": 0.25, "Medium": 0.5, "High": 0.75, "Ultra": 1.0}
        pass

    def _volume_down(self) -> None:
        vol = max(0.0, self._app.audio.master_volume - 0.1)
        self._app.audio.master_volume = vol
        if self._volume_bar is not None:
            self._volume_bar.value = vol

    def _volume_up(self) -> None:
        vol = min(1.0, self._app.audio.master_volume + 0.1)
        self._app.audio.master_volume = vol
        if self._volume_bar is not None:
            self._volume_bar.value = vol

    def _go_back(self) -> None:
        self._app.scene_manager.pop_with(
            SlideTransition(duration=0.3, direction="right"),
        )
