"""
Demonstrates the new UI widgets: Slider, Checkbox, RadioGroup.

What this example shows:
- Slider for continuous value selection
- Checkbox for boolean toggles
- RadioGroup for mutually exclusive options
- All widgets with keyboard navigation (Tab to focus)

Controls:
    Tab / Shift+Tab — navigate focus
    Arrow keys      — adjust focused Slider or RadioGroup
    Space / Enter   — toggle focused Checkbox
    ESC             — quit

Run from the repo root:
    python -m examples.example_widgets
"""

from __future__ import annotations
import pygame
from pygame_engine.app import Application, AppConfig
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Panel, Stack
from pygame_engine.ui.controls.checkbox import Checkbox
from pygame_engine.ui.controls.radio_group import RadioGroup
from pygame_engine.ui.controls.slider import Slider


class WidgetsExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
        self._output: Label | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        panel_rect = anchor(screen, (520, 460), "center")
        panel = Panel(panel_rect, manage_focus=True)

        rows = column(panel_rect, count=9, item_size=(440, 40),
                      spacing=8, padding=theme.spacing.xl)

        # Title
        title = Label(pygame.Rect(panel_rect.x, panel_rect.y - 52,
                                  panel_rect.width, 40),
                      "Widget Demo", font_size=theme.typography.xl,
                      colour=theme.colours.text, align="center")

        def make_row_label(row, text):
            return Label(pygame.Rect(rows[row].x, rows[row].y, 130, rows[row].height),
                         text, font_size=theme.typography.sm,
                         colour=theme.colours.text_secondary)

        # Sliders
        panel.add(make_row_label(0, "Volume"))
        vol_slider = Slider(pygame.Rect(rows[0].x+140, rows[0].y, 300, 24),
                            value=0.7, on_change=lambda v: self._log(f"Volume: {v:.0%}"))
        panel.add(vol_slider)

        panel.add(make_row_label(1, "Brightness"))
        bright_slider = Slider(pygame.Rect(rows[1].x+140, rows[1].y, 300, 24),
                               value=0.5, min_value=0.1, max_value=1.0,
                               on_change=lambda v: self._log(f"Brightness: {v:.0%}"))
        panel.add(bright_slider)

        # Checkboxes
        panel.add(make_row_label(2, "Options"))
        panel.add(Checkbox(pygame.Rect(rows[2].x+140, rows[2].y, 200, 36),
                           label="Fullscreen",
                           on_change=lambda v: self._log(f"Fullscreen: {v}")))
        panel.add(Checkbox(pygame.Rect(rows[2].x+350, rows[2].y, 200, 36),
                           label="VSync", checked=True,
                           on_change=lambda v: self._log(f"VSync: {v}")))

        panel.add(make_row_label(3, ""))
        panel.add(Checkbox(pygame.Rect(rows[3].x+140, rows[3].y, 220, 36),
                           label="Show FPS",
                           on_change=lambda v: self._log(f"Show FPS: {v}")))
        panel.add(Checkbox(pygame.Rect(rows[3].x+370, rows[3].y, 180, 36),
                           label="Subtitles", checked=True,
                           on_change=lambda v: self._log(f"Subtitles: {v}")))

        # RadioGroup
        panel.add(make_row_label(4, "Quality"))
        panel.add(RadioGroup(pygame.Rect(rows[4].x+140, rows[4].y, 300, 36*3+8),
                             options=["Low", "Medium", "High"],
                             selected_index=1,
                             on_change=lambda i, v: self._log(f"Quality: {v}")))

        # Output label
        self._output = Label(
            pygame.Rect(panel_rect.x, panel_rect.bottom + 16, panel_rect.width, 28),
            "Interact with the widgets above",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            align="center",
        )

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(title)
        root.add(self._output)
        self.root_widget = root

    def _log(self, msg: str) -> None:
        if self._output:
            self._output.text = msg

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        from pygame_engine.input import actions
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((22, 22, 30))
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(title="pygame_engine — widgets", width=1280, height=720))
    app.run(WidgetsExampleScene(app))

if __name__ == "__main__":
    run()
