# MY_GAME

A game built on [pygame_engine](../pygame_engine/).

---

## Getting started

### 1. Copy this template

```bash
cp -r template/ my_game/
cd my_game/
```

### 2. Install the engine

From the repo root:

```bash
pip install -e ../pygame_engine
```

Or if pygame_engine is already installed:

```bash
pip install pygame-ce
```

### 3. Rename the game

Search and replace `MY_GAME` with your game title in:
- `main.py`
- `README.md`

### 4. Run it

```bash
python main.py
```

You should see the main menu with Start, Settings, and Quit buttons.

---

## Project structure

```
my_game/
├── assets/
│   ├── fonts/          ← .ttf font files
│   ├── images/
│   │   ├── ui/         ← UI images (buttons, panels, icons)
│   │   └── sprites/    ← game sprites and spritesheets
│   └── sounds/         ← .wav and .ogg audio files
├── game/
│   ├── actions.py      ← all input action constants (engine + game)
│   ├── scenes/
│   │   ├── main_menu.py    ← main menu (Start, Settings, Quit)
│   │   ├── game_scene.py   ← your gameplay — fill this in
│   │   ├── pause_scene.py  ← pause overlay
│   │   └── settings_scene.py ← settings overlay
│   ├── ui/             ← game-specific composite widgets
│   ├── systems/        ← gameplay logic (movement, combat, AI, etc.)
│   └── models/         ← domain objects (Player, World, Item, etc.)
├── saves/              ← save files written by SaveManager
├── main.py             ← entry point
└── README.md
```

---

## Development workflow

### Adding a new scene

1. Create `game/scenes/my_scene.py`
2. Subclass `Scene` from `pygame_engine.scene`
3. Implement `on_enter`, `on_exit`, `_handle_event_scene`, `update`, `render`
4. Navigate to it from another scene using `app.scene_manager`

```python
from pygame_engine.scene import Scene
from pygame_engine.scene.transitions import FadeTransition

class MyScene(Scene):
    def __init__(self, app):
        super().__init__()
        self._app = app

    def on_enter(self):
        # Build UI, load assets, start music
        pass

    def render(self, surface):
        surface.fill((20, 20, 30))
        super().render(surface)
```

### Adding a game-specific action

1. Add a constant to `game/actions.py`
2. Add a keybinding in `main.py` → `_build_bindings()`
3. Query it in scenes with `app.input_manager.was_action_pressed(actions.MY_ACTION)`

### Loading assets

```python
# In on_enter:
image  = self._app.assets.image("ui/logo.png")
font   = self._app.assets.font("my_font.ttf", size=24)
sound  = self._app.assets.sound("ui_click.wav")
frames = self._app.assets.spritesheet("player.png", 48, 48)
```

### Playing audio

```python
self._app.audio.play_music(self._app.assets.asset_root / "sounds" / "theme.ogg")
self._app.audio.play_sfx(self._app.assets.sound("click.wav"))
self._app.audio.master_volume = 0.8
```

### Saving and loading

```python
from pygame_engine.persistence import SaveManager
from pathlib import Path

saves = SaveManager(Path("saves"), game_id="my_game", current_version=1)

# Save
saves.save("slot_1", {"level": 3, "gold": 120, "player_x": 64.0})

# Load
payload = saves.load_payload("slot_1")
```

### Animating sprites

```python
from pygame_engine.animation import SpriteAnimation, AnimationPlayer
from pygame_engine.graphics.sprite_renderer import draw_animation_frame

frames = self._app.assets.spritesheet("player.png", 48, 48)
anim   = AnimationPlayer()
anim.add("idle", SpriteAnimation("idle", frames[0:4], frame_duration=0.15))
anim.add("run",  SpriteAnimation("run",  frames[4:12], frame_duration=0.08))
anim.play("idle")

# Each frame:
anim.update(dt)
draw_animation_frame(surface, anim, player_rect)
```

### Debug overlay

Press **F1** in-game to toggle the debug overlay (FPS, scene, flags).
Press **F2** to dump the scene/widget tree to the console.

Enable debug mode in `main.py` by setting `debug=True` in `AppConfig`.

---

## Customising the theme

```python
from dataclasses import replace
from pygame_engine.theme import get_theme, set_theme

# In main() before app.run():
theme = get_theme()
my_theme = replace(theme,
    button=replace(theme.button,
        normal=replace(theme.button.normal, bg=(80, 40, 120))
    )
)
app.set_theme(my_theme)
```

---

## Key engine imports

```python
# App
from pygame_engine.app import Application, AppConfig

# Scenes
from pygame_engine.scene import Scene, SceneManager
from pygame_engine.scene.transitions import FadeTransition, SlideTransition, CrossfadeTransition

# UI
from pygame_engine.ui import Widget, Panel, Stack, Scrollable
from pygame_engine.ui import Button, InputField, ProgressBar
from pygame_engine.ui import Label, TextBlock
from pygame_engine.ui import Toast, Tooltip

# Layout
from pygame_engine.layout import anchor, row, column, grid

# Theme
from pygame_engine.theme import get_theme, set_theme

# Input
from pygame_engine.input import actions
from game.actions import ATTACK, INTERACT   # game-specific

# Animation
from pygame_engine.animation import Tween, SpriteAnimation, AnimationPlayer
from pygame_engine.animation.easing import ease_out_cubic

# Persistence
from pygame_engine.persistence import SaveManager

# Utils
from pygame_engine.utils.timers import Timer, Cooldown
from pygame_engine.utils.mathx  import lerp, clamp
```
