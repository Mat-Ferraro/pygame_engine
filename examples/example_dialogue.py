"""
What this example shows:
- Linear dialogue (press Space/Enter to advance)
- Branching dialogue with choice buttons
- Typewriter effect
- on_complete callback
- on_action callback for game events

Controls:
    Space / Enter / click — advance or complete typewriter
    1 / 2 / 3            — select choice by number
    R                    — restart dialogue
    ESC                  — quit

Run from the repo root:
    python -m examples.example_dialogue
"""

from __future__ import annotations
import pygame
from pygame_engine.app import Application, AppConfig
from pygame_engine.dialogue import DialogueBox, DialogueRunner, DialogueScript
from pygame_engine.layout import anchor
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Stack

SCRIPT = {
    "start": {
        "speaker": "Merchant",
        "text":    "Welcome, traveller! I have rare wares today.",
        "next":    "offer",
    },
    "offer": {
        "speaker": "Merchant",
        "text":    "Interested in my goods?",
        "choices": [
            {"label": "Show me what you have.",  "next": "show",    "action": "browse"},
            {"label": "Tell me about yourself.", "next": "story"},
            {"label": "No thanks.",              "next": "decline"},
        ],
    },
    "show": {
        "speaker": "Merchant",
        "text":    "Behold! A legendary sword, a healing potion, and a mysterious map.",
        "next":    "end_buy",
    },
    "end_buy": {"text": ""},
    "story": {
        "speaker": "Merchant",
        "text":    "I have travelled these roads for thirty years. Every scar tells a story.",
        "next":    "story2",
    },
    "story2": {
        "speaker": "Merchant",
        "text":    "But enough about me. Are you buying?",
        "choices": [
            {"label": "Yes, show me your wares.", "next": "show"},
            {"label": "Not today.",               "next": "decline"},
        ],
    },
    "decline": {
        "speaker": "Merchant",
        "text":    "Your loss. Safe travels.",
        "next":    "end_decline",
    },
    "end_decline": {"text": ""},
}


class DialogueExampleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._runner: DialogueRunner | None = None
        self._box:    DialogueBox   | None = None
        self._status_label: Label   | None = None

    def on_enter(self) -> None:
        screen = self._app.screen_rect
        theme  = get_theme()

        root = Stack(pygame.Rect(screen))

        hints = [
            "Space/Enter/Click — advance or complete typewriter",
            "1/2/3 — select choice   R — restart   ESC — quit",
        ]
        for i, hint in enumerate(hints):
            root.add(Label(pygame.Rect(12, 12 + i * 22, 600, 20), hint,
                           font_size=theme.typography.xs,
                           colour=theme.colours.text_secondary))

        self._status_label = Label(
            anchor(screen, (400, 24), "top_right", margin=12),
            "Status: running", font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="right",
        )
        root.add(self._status_label)

        box_rect = pygame.Rect(
            60, screen.height - 220,
            screen.width - 120, 180,
        )
        script = DialogueScript(SCRIPT)
        self._runner = DialogueRunner(script)
        self._runner.on_complete = self._on_complete
        self._runner.on_action   = self._on_action
        self._box = DialogueBox(box_rect, self._runner,
                                on_advance=lambda: self._runner.advance(),
                                chars_per_sec=35.0)
        root.add(self._box)
        self.root_widget = root
        self._runner.start()

    def _on_complete(self) -> None:
        if self._status_label:
            self._status_label.text = "Status: dialogue complete — press R to restart"

    def _on_action(self, tag: str, node) -> None:
        if self._status_label:
            self._status_label.text = f"Action fired: '{tag}'"

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        from pygame_engine.input import actions
        inp = self._app.input_manager
        if inp.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            if self._runner: self._runner.start()
            if self._status_label: self._status_label.text = "Status: running"
            return True
        return False

    def update(self, dt: float) -> None:
        if self._box: self._box.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((22, 22, 30))
        super().render(surface)


def run() -> None:
    app = Application(AppConfig(title="pygame_engine — dialogue", width=1280, height=720))
    app.run(DialogueExampleScene(app))

if __name__ == "__main__":
    run()
