"""
pygame_engine.dialogue

Script-driven dialogue system with typewriter rendering and branching.

Public API::

    from pygame_engine.dialogue import DialogueBox, DialogueRunner, DialogueScript

    script = DialogueScript({
        "start": {
            "speaker": "Guard",
            "text": "Halt! Who goes there?",
            "choices": [
                {"label": "A friend.", "next": "friendly"},
                {"label": "None of your business.", "next": "hostile"},
            ]
        },
        "friendly": {"speaker": "Guard", "text": "Pass.", "next": "end"},
        "hostile":  {"speaker": "Guard", "text": "Seize them!", "next": "end"},
        "end": {"text": ""},
    })

    runner = DialogueRunner(script)
    runner.on_complete = lambda: scene.end_dialogue()

    box = DialogueBox(
        rect=pygame.Rect(60, 480, 800, 180),
        runner=runner,
        on_advance=lambda: runner.advance(),
    )

    runner.start()

    # Each frame:
    box.update(dt)
    box.render(surface)
"""

from pygame_engine.dialogue.box import DialogueBox
from pygame_engine.dialogue.runner import DialogueRunner
from pygame_engine.dialogue.script import Choice, DialogueNode, DialogueScript

__all__ = [
    "DialogueBox",
    "DialogueRunner",
    "DialogueScript",
    "DialogueNode",
    "Choice",
]
