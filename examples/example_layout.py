"""
Demonstrates anchor, row, column, and grid layout helpers.
"""

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column, grid, row
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Panel, Stack


class LayoutExampleScene(Scene):
    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0, self._app.config.width, self._app.config.height)
        theme = get_theme()

        title = Label(
            pygame.Rect(0, 20, screen.width, 36),
            "Layout Demo",
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        )

        left_panel = Panel(anchor(screen, (360, 280), "top_left", margin=40))
        left_title = Label(
            pygame.Rect(left_panel.rect.x, left_panel.rect.y - 36, left_panel.rect.width, 28),
            "Row / Column",
            font_size=theme.typography.lg,
            colour=theme.colours.text,
            align="center",
        )

        row_rects = row(
            pygame.Rect(left_panel.rect.x + 20, left_panel.rect.y + 36, left_panel.rect.width - 40, 60),
            count=3,
            item_size=(86, 40),
            spacing=12,
        )
        col_rects = column(
            pygame.Rect(left_panel.rect.x + 20, left_panel.rect.y + 126, left_panel.rect.width - 40, 120),
            count=3,
            item_size=(240, 32),
            spacing=10,
        )

        right_panel = Panel(anchor(screen, (520, 420), "top_right", margin=40))
        right_title = Label(
            pygame.Rect(right_panel.rect.x, right_panel.rect.y - 36, right_panel.rect.width, 28),
            "Grid / Anchor",
            font_size=theme.typography.lg,
            colour=theme.colours.text,
            align="center",
        )

        grid_rects = grid(
            pygame.Rect(right_panel.rect.x + 24, right_panel.rect.y + 30, right_panel.rect.width - 48, 210),
            columns=4,
            count=8,
            item_size=(84, 54),
            spacing=10,
        )

        anchored = Label(
            anchor(right_panel.rect, (180, 28), "bottom", margin=28),
            "Anchored bottom-center",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            align="center",
        )

        root = Stack(pygame.Rect(screen))

        root.add(title)
        root.add(left_title)
        root.add(right_title)
        root.add(left_panel)
        root.add(right_panel)
        root.add(anchored)

        for i, rect in enumerate(row_rects, start=1):
            left_panel.add(_ColourSwatch(rect, f"R{i}", (72 + i * 20, 110, 200)))

        for i, rect in enumerate(col_rects, start=1):
            left_panel.add(_ColourSwatch(rect, f"Column {i}", (90, 90 + i * 28, 120)))

        for i, rect in enumerate(grid_rects, start=1):
            right_panel.add(_ColourSwatch(rect, str(i), (80, 130 + i * 8, 150)))

        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


class _ColourSwatch(Label):
    def __init__(self, rect: pygame.Rect, text: str, colour: tuple[int, int, int]) -> None:
        super().__init__(rect, text, align="center")
        self._fill = colour

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        pygame.draw.rect(surface, self._fill, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1, border_radius=6)
        super().render(surface)


def run() -> None:
    config = AppConfig(
        title="pygame_engine — layout demo",
        width=1280,
        height=720,
        target_fps=60,
        resizable=True,
    )
    app = Application(config)
    app.run(LayoutExampleScene(app))


if __name__ == "__main__":
    run()
