"""
examples/example_scene.py

Demonstrates scene stack behaviour:
- push
- pop
- replace
- overlay blocking flags
"""

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.input import actions
from pygame_engine.layout import anchor, column
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, TextBlock


class SceneMenu(Scene):
    blocks_input_below = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0, self._app.config.width, self._app.config.height)
        theme = get_theme()

        panel_rect = anchor(screen, (520, 420), "center")
        panel = Panel(panel_rect)

        title = Label(
            pygame.Rect(panel_rect.x, panel_rect.y - 56, panel_rect.width, 40),
            "Scene Stack Demo",
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        )

        info = TextBlock(
            pygame.Rect(panel_rect.x + 28, panel_rect.y + 28, panel_rect.width - 56, 96),
            "Push an overlay, replace this scene, or return from the alternate scene. "
            "This example is meant to demonstrate scene flow rather than final UI.",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            padding=0,
            line_spacing=6,
        )

        rects = column(
            pygame.Rect(panel_rect.x, panel_rect.y + 150, panel_rect.width, 180),
            count=3,
            item_size=(260, 48),
            spacing=14,
        )

        push_btn = Button(rects[0], "Push Overlay", on_click=lambda: self._app.scene_manager.push(OverlayScene(self._app)))
        replace_btn = Button(rects[1], "Replace Scene", on_click=lambda: self._app.scene_manager.replace(AlternateScene(self._app)))
        quit_btn = Button(rects[2], "Quit", on_click=self._app.stop)

        panel.add(info)
        panel.add(push_btn)
        panel.add(replace_btn)
        panel.add(quit_btn)

        root = Panel(pygame.Rect(screen), draw_background=False, draw_border=False)
        root.add(title)
        root.add(panel)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)


class AlternateScene(Scene):
    blocks_input_below = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0, self._app.config.width, self._app.config.height)
        theme = get_theme()

        panel_rect = anchor(screen, (520, 320), "center")
        panel = Panel(panel_rect)

        title = Label(
            pygame.Rect(panel_rect.x, panel_rect.y - 56, panel_rect.width, 40),
            "Alternate Scene",
            font_size=theme.typography.xl,
            colour=theme.colours.text,
            align="center",
        )

        body = TextBlock(
            pygame.Rect(panel_rect.x + 24, panel_rect.y + 24, panel_rect.width - 48, 120),
            "This scene was reached via replace(). Going back will replace it with a fresh menu scene.",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            line_spacing=6,
        )

        back_rect = anchor(pygame.Rect(panel_rect.x, panel_rect.y + 210, panel_rect.width, 60), (240, 48), "center")
        back = Button(back_rect, "Back to Menu", on_click=lambda: self._app.scene_manager.replace(SceneMenu(self._app)))

        panel.add(body)
        panel.add(back)

        root = Panel(pygame.Rect(screen), draw_background=False, draw_border=False)
        root.add(title)
        root.add(panel)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.scene_manager.replace(SceneMenu(self._app))
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((24, 28, 42))
        super().render(surface)


class OverlayScene(Scene):
    blocks_input_below = True
    blocks_update_below = True
    blocks_render_below = False

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self) -> None:
        screen = pygame.Rect(0, 0, self._app.config.width, self._app.config.height)
        theme = get_theme()

        dialog_rect = anchor(screen, (440, 220), "center")
        dialog = Panel(dialog_rect)

        title = Label(
            pygame.Rect(dialog_rect.x, dialog_rect.y + 24, dialog_rect.width, 32),
            "Overlay Scene",
            font_size=theme.typography.lg,
            colour=theme.colours.text,
            align="center",
        )

        body = TextBlock(
            pygame.Rect(dialog_rect.x + 24, dialog_rect.y + 72, dialog_rect.width - 48, 74),
            "This overlay blocks input and update below it, but allows the scene underneath to remain visible.",
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary,
            align="center",
            line_spacing=6,
        )

        close_rect = anchor(pygame.Rect(dialog_rect.x, dialog_rect.y + 150, dialog_rect.width, 50), (180, 44), "center")
        close_btn = Button(close_rect, "Close Overlay", on_click=self._app.scene_manager.pop)

        dialog.add(title)
        dialog.add(body)
        dialog.add(close_btn)

        root = Panel(pygame.Rect(screen), draw_background=False, draw_border=False)
        root.add(dialog)
        self.root_widget = root

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.scene_manager.pop()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        surface.blit(shade, (0, 0))
        super().render(surface)


def run() -> None:
    config = AppConfig(
        title="pygame_engine — scene demo",
        width=1280,
        height=720,
        target_fps=60,
    )
    app = Application(config)
    app.run(SceneMenu(app))


if __name__ == "__main__":
    run()
