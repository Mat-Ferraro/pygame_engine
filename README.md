# pygame_engine

A lightweight, reusable framework built on top of pygame-ce.

`pygame_engine` gives you a clean, structured foundation for pygame projects
so you can focus on making your game instead of rebuilding the same
infrastructure every time.

---

## What it provides

- **Application runtime** — main loop, delta-time, window management
- **Stack-based scene system** — push/pop/replace scenes with full lifecycle hooks
- **UI widget library** — Button, Label, TextBlock, Panel, Stack, Toast, Tooltip
- **Layout helpers** — `row`, `column`, `grid`, `anchor` (stateless, composable)
- **Theme system** — design tokens → defaults → runtime, swappable at any time
- **Action-based input** — `was_action_pressed(CONFIRM)` not `is_key_down(K_RETURN)`
- **Asset loading** — lazy-cached images, fonts, and sounds via `app.assets`
- **Audio manager** — music streaming, SFX playback, volume controls, mute
- **Animation** — 30 easing functions, `Tween` for single-value animation
- **Graphics helpers** — draw utilities and alpha surface helpers
- **Utils** — `Timer`, `Cooldown`, colour math, rect helpers, math extensions

It is **not** a genre-specific gameplay engine. Physics, combat, inventory, and
progression belong in the projects built on top of it.

---

## Quick start

```python
from pygame_engine.app import Application, AppConfig
from pygame_engine.scene import Scene
from pygame_engine.ui import Button, Label, Panel
from pygame_engine.layout import anchor, column
from pygame_engine.input import actions
import pygame

class MainMenuScene(Scene):

    def __init__(self, app):
        super().__init__()
        self._app = app

    def on_enter(self):
        screen = pygame.Rect(0, 0,
                             self._app.config.width,
                             self._app.config.height)

        panel = Panel(anchor(screen, (280, 240), "center"))

        btn_rects = column(panel.rect, count=2,
                           item_size=(200, 52), spacing=12, padding=24)

        panel.add(Button(btn_rects[0], "Start",
                         on_click=lambda: print("Start!")))
        panel.add(Button(btn_rects[1], "Quit",
                         on_click=self._app.stop))

        self.root_widget = panel

    def _handle_event_scene(self, event):
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop()
            return True
        return False

    def render(self, surface):
        surface.fill((22, 22, 30))
        super().render(surface)


config = AppConfig(title="My Game", width=1280, height=720)
Application(config).run(MainMenuScene)
```

See `examples/` for runnable examples covering all major systems.

---

## Project layout

```
pygame_engine/              ← repo root
├── docs/                   ← architecture and system documentation
├── examples/               ← runnable examples (one per major system)
├── tests/                  ← automated test suite (pytest)
├── pygame_engine/          ← the importable package
│   ├── animation/          ← Tween, easing functions
│   ├── app/                ← Application, AppConfig
│   ├── assets/             ← AssetLoader, image/font/sound loading
│   ├── audio/              ← AudioManager, music and SFX
│   ├── graphics/           ← draw helpers, surface utilities
│   ├── input/              ← InputManager, actions, bindings
│   ├── layout/             ← row, column, grid, anchor
│   ├── scene/              ← Scene, SceneManager, SceneStack
│   ├── theme/              ← tokens, defaults, runtime
│   ├── ui/                 ← Widget, Panel, Stack, Button, Label, …
│   └── utils/              ← Timer, Cooldown, colors, rects, mathx
├── main.py                 ← development entry point
├── pyproject.toml
└── CHANGELOG.md
```

---

## Installation

Clone the repo and install in editable mode:

```bash
git clone <repo-url>
cd pygame_engine
pip install -e .
```

Requires Python 3.11+ and pygame-ce 2.4+.

---

## Running examples

```bash
python main.py
```

Switch between examples by editing the import in `main.py`.
Each example in `examples/` is also runnable directly:

```bash
python -m examples.example_buttons
python -m examples.example_feedback
python -m examples.example_scene
```

---

## Running tests

```bash
pytest
pytest -v        # verbose
pytest -v -s     # verbose + print output
```

---

## Common imports

```python
# Application
from pygame_engine.app import Application, AppConfig

# Scenes
from pygame_engine.scene import Scene, SceneManager, SceneStack

# UI
from pygame_engine.ui import Widget, Panel, Stack
from pygame_engine.ui import Button, Label, TextBlock
from pygame_engine.ui import Toast, Tooltip

# Layout
from pygame_engine.layout import anchor, row, column, grid

# Theme
from pygame_engine.theme import get_theme, set_theme, Theme

# Input
from pygame_engine.input import InputManager
from pygame_engine.input import actions

# Animation
from pygame_engine.animation import Tween
from pygame_engine.animation.easing import ease_out_cubic

# Assets and audio (via app)
app.assets.image("ui/button.png")
app.assets.font("inter.ttf", size=18)
app.audio.play_music("music/theme.ogg")
app.audio.play_sfx(app.assets.sound("click.wav"))

# Utils
from pygame_engine.utils.timers import Timer, Cooldown
from pygame_engine.utils.mathx  import lerp, clamp, smoothstep
from pygame_engine.utils.colors import lerp_color, hex_to_rgb
from pygame_engine.utils.rects  import inset, anchor as rect_anchor
```

---

## Documentation

All architecture decisions and system contracts live in `docs/`.

| Document | Contents |
|---|---|
| `architecture.md` | Overall system design and package responsibilities |
| `accepted_decisions.md` | Current accepted rules |
| `decision_log.md` | Historical decision record |
| `using_pygame_engine.md` | How to build a game on top of the engine |
| `scene_lifecycle.md` | Scene hooks and stack behaviour |
| `widget_contract.md` | Widget base contract and extension guide |
| `theme_system.md` | Token → default → runtime theme flow |
| `input_system.md` | Action/binding/state model |
| `layout_system.md` | Layout helper design and usage |
| `animation_system.md` | Easing functions and Tween |
| `asset_pipeline.md` | Asset loading, caching, path conventions |
| `audio_system.md` | Music, SFX, and volume management |
| `roadmap.md` | Phase plan and out-of-scope decisions |
