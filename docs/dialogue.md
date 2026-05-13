# Dialogue System

## Purpose

Script-driven dialogue for narrative games, RPGs, and adventure games.
Three components work together:

- **`DialogueScript`** — validates and holds the raw dialogue data
- **`DialogueRunner`** — pure state machine that advances through the script
- **`DialogueBox`** — widget that renders the current state with typewriter effect

The runner and script have no pygame dependency — they can be unit tested
headlessly. The box only reads from the runner and renders it.

---

## Quick start

```python
from pygame_engine.dialogue import DialogueBox, DialogueRunner, DialogueScript

# 1. Define the script
script = DialogueScript({
    "start": {
        "speaker": "Guard",
        "text": "Halt! Who goes there?",
        "choices": [
            {"label": "A friend.", "next": "friendly"},
            {"label": "None of your business.", "next": "hostile"},
        ]
    },
    "friendly": {"speaker": "Guard", "text": "Very well. Pass.", "next": "end"},
    "hostile":  {"speaker": "Guard", "text": "Then you shall not pass!", "next": "end"},
    "end": {"text": ""},
})

# 2. Create runner and box
runner = DialogueRunner(script)
runner.on_complete = lambda: self.end_dialogue()

box = DialogueBox(
    rect=pygame.Rect(60, 480, 800, 180),
    runner=runner,
    on_advance=lambda: runner.advance(),
)

# 3. Start it
runner.start()

# 4. Each frame in update() and render()
box.update(dt)
box.render(surface)
```

---

## Script format

A script is a plain Python dict mapping node IDs to node dicts.
It is JSON-compatible — load from a file with `json.load()`.

### Node fields

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | str | ✅ | Dialogue text to display. Empty string on end nodes. |
| `speaker` | str | — | Who is speaking. Absent or `""` = narration. |
| `next` | str | — | ID of the next node. Absent = end of dialogue. |
| `choices` | list | — | List of choice dicts. Overrides `next`. |
| `action` | str | — | Tag fired via `on_action` when this node is entered. |

### Choice fields

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | str | ✅ | Text shown on the choice button. |
| `next` | str | ✅ | Node ID to advance to when selected. |
| `action` | str | — | Tag fired via `on_action` when this choice is selected. |

### End nodes

A node ends the dialogue when it has no `next` and no `choices`. By
convention, end nodes have `"text": ""` so the box renders nothing:

```python
"end": {"text": ""}
```

### Example — linear dialogue

```python
{
    "start":  {"speaker": "Innkeeper", "text": "Welcome, traveller!",  "next": "b"},
    "b":      {"speaker": "Innkeeper", "text": "Need a room?",         "next": "end"},
    "end":    {"text": ""},
}
```

### Example — branching dialogue

```python
{
    "start": {
        "speaker": "Merchant",
        "text": "I have rare goods. Interested?",
        "choices": [
            {"label": "Show me.",         "next": "show"},
            {"label": "Not right now.",   "next": "decline"},
        ]
    },
    "show":    {"speaker": "Merchant", "text": "Behold!",   "next": "end"},
    "decline": {"speaker": "Merchant", "text": "Your loss.", "next": "end"},
    "end": {"text": ""},
}
```

### Example — actions

```python
{
    "start": {
        "text": "The ancient door swings open.",
        "action": "door_open",
        "next": "end",
    },
    "end": {"text": ""},
}
```

---

## DialogueRunner

```python
runner = DialogueRunner(script)

# Callbacks (set before start)
runner.on_complete   = lambda: end_dialogue()
runner.on_action     = lambda tag, node: game.fire_event(tag)
runner.on_node_enter = lambda node: audio.play_voice(node.node_id)

runner.start()              # begin from start_node
runner.start("mid_scene")   # begin from specific node

# Advance (no choices)
runner.advance()

# Branch (when has_choices is True)
runner.select_choice(0)     # select by index
# or let the box handle it automatically

# Jump directly to a node (cutscene skip, conditional branch)
runner.jump("boss_fight_intro")

# Query state
runner.current_node     # DialogueNode | None
runner.has_choices      # True if player must choose
runner.choices          # list of Choice objects
runner.is_complete      # True when dialogue ended
runner.is_started       # True after start()

runner.reset()          # back to unstarted state
```

---

## DialogueBox

```python
box = DialogueBox(
    rect=pygame.Rect(60, 480, 800, 180),
    runner=runner,
    on_advance=lambda: runner.advance(),     # called on Space/Enter/click
    on_choice=lambda i: runner.select_choice(i),  # optional; default handles it
    chars_per_sec=40.0,   # typewriter speed. 0 = instant
)

# Each frame
box.update(dt)
box.render(surface)
```

### Input handling (automatic)

| Input | Effect |
|---|---|
| Space / Enter / click | If revealing: complete reveal instantly. If complete: call `on_advance`. |
| Keys 1–9 | Select choice by index (when choices visible) |
| Click on choice button | Select that choice |

### Typewriter

```python
box.is_revealing       # True while text is still printing
box.complete_reveal()  # instantly show all text
```

---

## Patterns

### Dialogue as a scene overlay

```python
class DialogueOverlay(Scene):
    blocks_input_below  = True
    blocks_render_below = False

    def __init__(self, app, script):
        super().__init__()
        self._app    = app
        self._runner = DialogueRunner(script)
        self._runner.on_complete = self._on_done
        self._box    = DialogueBox(
            rect=pygame.Rect(60, app.screen_rect.height - 220, 
                             app.screen_rect.width - 120, 180),
            runner=self._runner,
            on_advance=lambda: self._runner.advance(),
        )

    def on_enter(self):
        self._runner.start()

    def update(self, dt):
        self._box.update(dt)

    def render(self, surface):
        self._box.render(surface)

    def overlay_render(self, surface):
        pass   # no floating UI needed here

    def _on_done(self):
        self._app.scene_manager.pop()
```

### Triggering from a game scene

```python
def _check_npc_interaction(self):
    if player_near_npc and input_manager.was_action_pressed(INTERACT):
        self._app.scene_manager.push(
            DialogueOverlay(self._app, npc.dialogue_script)
        )
```

### Loading script from JSON

```python
import json
from pathlib import Path
from pygame_engine.dialogue import DialogueScript

raw    = json.loads(Path("data/dialogue/guard.json").read_text())
script = DialogueScript(raw, start_node="greeting")
```

### Conditional branches from game code

```python
# Jump to a different branch based on game state
def on_node_enter(node):
    if node.node_id == "check_quest" and player.has_quest_item:
        runner.jump("quest_complete")
    elif node.node_id == "check_quest":
        runner.jump("quest_incomplete")

runner.on_node_enter = on_node_enter
```

---

## Accepted decisions

### Runner is a pure state machine with no rendering
`DialogueRunner` has no pygame imports. It can be unit tested headlessly
and reused in non-rendering contexts (cutscene logic, tests, tools).

### Script is validated at construction time
`DialogueScript` validates all `next` references on construction. Broken
scripts raise `ValueError` immediately rather than crashing at runtime
mid-dialogue.

### Empty text + no next = auto-complete
A node with `text=""` and no `next` and no `choices` immediately marks
the dialogue complete. This is the canonical end-node pattern — it
prevents the box from briefly rendering a blank frame.

### Box drives runner via callbacks, not directly
`DialogueBox` calls `on_advance` and `on_choice` callbacks rather than
calling `runner.advance()` directly. This lets games intercept advances
for logging, analytics, save-game triggers, or conditional branches.

### No built-in portrait/voice system
The box renders a speaker name bar but no portrait image. Games hook
`runner.on_node_enter` to show portraits, play voice lines, or trigger
animations. The system stays generic.
