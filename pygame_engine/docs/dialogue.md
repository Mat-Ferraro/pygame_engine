# Dialogue System

## Purpose

Script-driven dialogue for narrative games, RPGs, and adventure games.

- **`DialogueScript`** — validates and holds the raw dialogue data
- **`DialogueRunner`** — pure state machine that advances through the script
- **`DialogueBox`** — widget that renders the current state with typewriter effect

---

## Quick start

```python
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
runner.on_complete = lambda: self.end_dialogue()

box = DialogueBox(
    rect=pygame.Rect(60, 480, 800, 180),
    runner=runner,
    on_advance=lambda: runner.advance(),
)
runner.start()

# Each frame:
box.update(dt)
box.render(surface)
```

---

## Script format

| Field | Required | Description |
|---|---|---|
| `text` | ✅ | Dialogue text. Empty `""` on end nodes. |
| `speaker` | — | Who is speaking. Absent = narration. |
| `next` | — | Next node ID. Absent = end. |
| `choices` | — | List of `{label, next, action?}`. Overrides `next`. |
| `action` | — | Tag fired via `on_action` when node is entered. |

End nodes: `{"text": ""}` — auto-completes when reached.

---

## DialogueRunner

```python
runner = DialogueRunner(script)
runner.on_complete    = lambda: end_dialogue()
runner.on_action      = lambda tag, node: game.fire(tag)
runner.on_node_enter  = lambda node: audio.play_voice(node.node_id)

runner.start()
runner.start("mid_scene")   # custom start node
runner.advance()
runner.select_choice(0)
runner.jump("boss_intro")
runner.reset()

runner.current_node    # DialogueNode | None
runner.has_choices     # True if player must choose
runner.choices         # list of Choice
runner.is_complete
```

---

## DialogueBox

Input (automatic):
- Space / Enter / click — complete typewriter or advance
- Keys 1–9 — select choice by index
- Click on choice button — select choice

```python
box.is_revealing       # True while typewriter is printing
box.complete_reveal()  # instant reveal
```

---

## Dialogue as a scene overlay

```python
class DialogueOverlay(Scene):
    blocks_render_below = False
    def __init__(self, app, script):
        super().__init__()
        self._runner = DialogueRunner(script)
        self._runner.on_complete = lambda: app.scene_manager.pop()
        self._box = DialogueBox(
            rect=pygame.Rect(60, app.screen_rect.height - 220,
                             app.screen_rect.width - 120, 180),
            runner=self._runner,
            on_advance=lambda: self._runner.advance(),
        )
    def on_enter(self): self._runner.start()
    def update(self, dt): self._box.update(dt)
    def render(self, surface): self._box.render(surface)
```

## Loading from JSON

```python
import json
script = DialogueScript(json.loads(Path("data/guard.json").read_text()))
```

## Conditional branches

```python
def on_node_enter(node):
    if node.node_id == "check_quest":
        runner.jump("done" if player.has_item else "need_item")
runner.on_node_enter = on_node_enter
```
