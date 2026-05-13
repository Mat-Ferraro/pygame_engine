A practical guide for building a game project on top of `pygame_engine`.

---

## What the engine provides vs what your game provides

| Engine | Your game |
|---|---|
| Application runtime and main loop | Gameplay rules and systems |
| Scene flow and stack management | Game-specific scenes |
| UI widget library | Composite widgets (inventory cards, HUD panels, etc.) |
| Layout, theme, input abstraction | Game-specific keybindings and theme overrides |
| Asset loading and caching | Asset files and directory structure |
| Audio playback and volume control | Music tracks and sound effects |
| Animation (Tween, easing) | Animated game objects |
| Generic utils (timers, math, rects) | Domain models and game entities |

The engine stays generic. Your game contains the unique behaviour.

---

## Starting a new game project

### Recommended project structure

```
my_game/
├── assets/
│   ├── fonts/
│   ├── images/
│   │   ├── ui/
│   │   └── sprites/
│   └── sounds/
├── game/
│   ├── scenes/         ← your Scene subclasses
│   ├── ui/             ← composite widgets built from engine widgets
│   ├── systems/        ← gameplay logic
│   └── models/         ← domain objects (Player, World, etc.)
└── main.py
```

### Minimal entry point

```python
# main.py
from pygame_engine.app import Application, AppConfig
from game.scenes.main_menu import MainMenuScene

config = AppConfig(
    title="My Game",
    width=1280,
    height=720,
    target_fps=60,
    asset_root=Path("assets"),
)
Application(config).run(MainMenuScene)
```

---

## Scenes

Subclass `Scene` for each high-level application state.

```python
from pygame_engine.scene import Scene
import pygame

class MainMenuScene(Scene):

    # Blocking policy (all True by default — a full-screen scene)
    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app):
        super().__init__()
        self._app = app

    def on_enter(self):
        """Called once when this scene becomes active. Build your UI here."""
        ...

    def on_exit(self):
        """Called once when this scene is permanently removed."""
        ...

    def on_pause(self):
        """Called when another scene is pushed on top of this one."""
        ...

    def on_resume(self):
        """Called when the scene above this one is popped."""
        ...

    def _handle_event_scene(self, event):
        """Scene-level input handling (after root_widget gets first look)."""
        return False

    def update(self, dt):
        super().update(dt)   # delegates to root_widget

    def render(self, surface):
        surface.fill((22, 22, 30))
        super().render(surface)  # delegates to root_widget
```

### Scene transitions

```python
from pygame_engine.scene import FadeTransition, SlideTransition, CrossfadeTransition

# Without transition:
app.scene_manager.push(PauseScene(app))
app.scene_manager.replace(GameplayScene(app))
app.scene_manager.pop()
app.scene_manager.clear_and_push(MainMenuScene(app))

# With transition:
app.scene_manager.push_with(PauseScene(app), SlideTransition(0.3, 'down'))
app.scene_manager.replace_with(GameplayScene(app), FadeTransition(0.4))
app.scene_manager.pop_with(CrossfadeTransition(0.25))
```

---

## UI

### Building a screen

```python
from pygame_engine.ui import Button, Label, Panel, Stack
from pygame_engine.layout import anchor, column
from pygame_engine.theme.runtime import get_theme
import pygame

def build_main_menu(app):
    screen = pygame.Rect(0, 0, app.config.width, app.config.height)
    theme  = get_theme()

    # A centred panel
    panel = Panel(anchor(screen, (300, 320), "center"))

    # Title above the panel
    title = Label(
        pygame.Rect(panel.rect.x, panel.rect.y - 56, panel.rect.width, 44),
        "My Game",
        font_size=theme.typography.xxl,
        align="center",
    )

    # Buttons laid out in a column inside the panel
    btn_rects = column(panel.rect, count=3,
                       item_size=(220, 52), spacing=12,
                       padding=theme.spacing.xl)

    panel.add(Button(btn_rects[0], "New Game", on_click=...))
    panel.add(Button(btn_rects[1], "Options",  on_click=...))
    panel.add(Button(btn_rects[2], "Quit",     on_click=app.stop))

    # Use Stack as a transparent root to hold all top-level widgets
    root = Stack(pygame.Rect(screen))
    root.add(panel)
    root.add(title)
    return root
```

Assign the result to `self.root_widget` in `on_enter`.

If your scene uses a `Dropdown` or floating `Tooltip`, override
`overlay_render()` so the floating list appears above all other widgets:

```python
def overlay_render(self, surface):
    self._resolution_dropdown.overlay_render(surface)
```

### Available widgets

| Widget | Purpose |
|---|---|
| `Widget` | Base class for custom widgets |
| `Panel` | Themed background + child management (opt-in focus traversal) |
| `Stack` | Transparent grouping container (opt-in focus traversal) |
| `Scrollable` | Clipping viewport with mouse-wheel scroll |
| `Button` | Clickable with `on_click` callback; keyboard-activatable when focused |
| `Dropdown` | Option selector with floating list via `overlay_render()` |
| `InputField` | Single-line text entry with cursor, placeholder, password mode |
| `ProgressBar` | Horizontal or vertical fill bar |
| `Label` | Single-line text display |
| `TextBlock` | Multi-line wrapped text with render caching |
| `Toast` | Auto-dismissing notification |
| `Tooltip` | Mouse-following context hint |

### Building custom widgets

```python
from pygame_engine.ui.base.widget import Widget
from pygame_engine.theme.runtime import get_theme
import pygame

class HealthBar(Widget):

    def __init__(self, rect, max_hp):
        super().__init__(rect)
        self.max_hp  = max_hp
        self.current = max_hp

    def render(self, surface):
        if not self.visible:
            return
        theme = get_theme()
        ratio = max(0.0, self.current / self.max_hp)
        filled = pygame.Rect(self.rect.x, self.rect.y,
                             int(self.rect.width * ratio), self.rect.height)
        pygame.draw.rect(surface, (180, 60, 60), self.rect, border_radius=4)
        pygame.draw.rect(surface, (60, 200, 80), filled, border_radius=4)
```

---

## Input

Use action queries rather than raw key checks:

```python
from pygame_engine.input import actions

# In _handle_event_scene or a widget's _handle_event_widget:
def _handle_event_scene(self, event):
    if self._app.input_manager.was_action_pressed(actions.CONFIRM):
        self._on_confirm()
        return True
    if self._app.input_manager.is_action_down(actions.NAV_UP):
        self._scroll_up()
        return True
    return False
```

### Adding game-specific actions

```python
# game/input_actions.py
from pygame_engine.input.actions import CONFIRM, CANCEL  # re-export engine actions

ATTACK   = "attack"
INTERACT = "interact"
SPRINT   = "sprint"
```

### Custom bindings

```python
import pygame
from pygame_engine.input.bindings import DEFAULT_BINDINGS
from game import input_actions

MY_BINDINGS = {
    **DEFAULT_BINDINGS,
    pygame.K_z:     input_actions.ATTACK,
    pygame.K_e:     input_actions.INTERACT,
    pygame.K_LSHIFT: input_actions.SPRINT,
}
```

Pass to `InputManager` or set on `app.input_manager.bindings` at startup.

---

## Theme

The engine ships with a complete default theme. Override what you need:

```python
from dataclasses import replace
from pygame_engine.theme import get_theme, set_theme

# Swap a single value
theme = get_theme()
new_theme = replace(theme,
    button=replace(theme.button,
        normal=replace(theme.button.normal, bg=(80, 40, 120))
    )
)
set_theme(new_theme)
```

Or call `app.set_theme(my_theme)` at startup before the first frame.

---

## Assets

```python
# Images (cached, convert_alpha by default)
logo  = app.assets.image("ui/logo.png")
tiles = app.assets.spritesheet("sprites/tileset.png",
                                frame_width=32, frame_height=32)

# Fonts (cached by path + size)
heading_font = app.assets.font("inter_bold.ttf", size=28)
body_font    = app.assets.sysfont("segoeui,arial", size=18)

# Sounds (None if missing — non-fatal)
click_sfx = app.assets.sound("ui_click.wav")
```

Asset root defaults to `Path("assets")` — override via `AppConfig.asset_root`.
Set `AppConfig.debug=True` to get placeholder surfaces for missing images.

---

## Audio

```python
# Music (streamed, one track at a time)
app.audio.play_music(app.assets.asset_root / "music" / "theme.ogg")
app.audio.stop_music(fade_out_ms=1000)
app.audio.pause_music()
app.audio.resume_music()

# Sound effects
click = app.assets.sound("ui_click.wav")
app.audio.play_sfx(click)
app.audio.play_sfx(click, volume=0.5)   # per-call volume multiplier

# Volume (0.0 – 1.0)
app.audio.master_volume = 0.8
app.audio.music_volume  = 0.6
app.audio.sfx_volume    = 1.0
app.audio.muted         = False
app.audio.toggle_mute()
```

---

## Animation

```python
from pygame_engine.animation import Tween
from pygame_engine.animation.easing import ease_out_back, ease_in_out_cubic

# Slide a panel in from off-screen
self._slide = Tween(start=-300, end=0, duration=0.4,
                    easing=ease_out_back, auto_start=True)

# In update():
self._slide.update(dt)
self._panel.rect.x = int(self._slide.value)

# Fade something in
self._fade = Tween(0.0, 1.0, 0.3, easing=ease_in_out_cubic, auto_start=True)
self._fade.update(dt)
surface.set_alpha(int(self._fade.value * 255))
```

---

## Timers

```python
from pygame_engine.utils.timers import Timer, Cooldown

# One-shot timer
self._spawn_delay = Timer(3.0, auto_start=True)
self._spawn_delay.update(dt)
if self._spawn_delay.is_done:
    self._spawn_enemy()

# Repeating interval
self._footstep = Cooldown(0.4, auto_start=True)
self._footstep.update(dt)
if self._footstep.fired:
    app.audio.play_sfx(footstep_sfx)
```

---

## Particles

```python
from pygame_engine.particles.presets import explosion, fire_emitter, trail

# One-shot burst
fx = explosion(enemy.x, enemy.y)
fx.burst(60)

# Continuous emitter
fire = fire_emitter(torch.x, torch.y, rate=40)
fire.start()

# Each frame
fx.update(dt)
fx.render(surface)   # alpha-blended
# or: fx.render_fast(surface)  # solid, faster for high counts

# Cull dead one-shots
effects = [fx for fx in effects if not fx.is_empty]
```

---

## Events

Use the event bus for loose coupling between game systems:

```python
from pygame_engine.events import bus

# Subscribe
bus.on('player.damaged', hud.on_player_damaged)
bus.once('tutorial.first_kill', show_tip)
bus.on('player.*', analytics.record)   # wildcard

# Emit (keyword args only)
bus.emit('player.damaged', amount=30, source='spike_trap')

# Unsubscribe
bus.off('player.damaged', hud.on_player_damaged)
bus.clear('player.damaged')   # remove all handlers for event
```

See `docs/event_model.md` for naming conventions and full API.

---

## Rules for game projects

1. Use engine primitives first — only build custom widgets when the engine doesn't cover the need.
2. Keep gameplay logic out of engine packages.
3. Keep game-specific scenes, models, and systems in your game repo.
4. If the same pattern appears across multiple projects, only then consider moving it into the engine.
5. Update engine docs when engine contracts change; update game docs for game decisions.
