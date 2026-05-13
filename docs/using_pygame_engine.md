---

## Quick start

```python
# main.py
from pathlib import Path
from pygame_engine.app import Application, AppConfig
from pygame_engine.debug.crash_log import crash_guard
from game.locale import load_locales
from game.scenes.main_menu import MainMenuScene

load_locales()
config = AppConfig(title="My Game", width=1280, height=720,
                   target_fps=60, asset_root=Path("assets"))
app = Application(config)
with crash_guard(Path("crash.log")):
    app.run(MainMenuScene(app))
```

---

## Scenes

```python
class MyScene(Scene):
    blocks_input_below  = True
    blocks_update_below = True
    blocks_render_below = True

    def __init__(self, app): super().__init__(); self._app = app
    def on_enter(self):  ...   # build UI, load assets
    def on_exit(self):   ...   # stop music, save state
    def on_pause(self):  ...   # pause timers
    def on_resume(self): ...   # resume timers
    def on_resize(self, width, height): ...   # rebuild layout
    def _handle_event_scene(self, event): return False
    def update(self, dt): super().update(dt)
    def render(self, surface): surface.fill(...); super().render(surface)
```

### Transitions
```python
app.scene_manager.push_with(PauseScene(app), SlideTransition(0.3, "down"))
app.scene_manager.replace_with(GameScene(app), FadeTransition(0.4))
app.scene_manager.pop_with(CrossfadeTransition(0.25))
```

---

## Window management

```python
app.set_resolution(1920, 1080)
app.set_fullscreen(True)
app.toggle_fullscreen()
screen = app.screen_rect         # always reflects current size

# Subscribe to resize/fullscreen events
from pygame_engine.events import bus
bus.on("window.resized",            lambda width, height: ...)
bus.on("window.fullscreen_changed", lambda fullscreen: ...)
```

Scenes override `on_resize()` to rebuild layout:
```python
def on_resize(self, width, height):
    self._layout.apply(pygame.Rect(0, 0, width, height))
```

---

## UI

### Available widgets
| Widget | Purpose |
|---|---|
| `Panel` | Themed background + child management |
| `Stack` | Transparent grouping container |
| `Scrollable` | Clipping viewport with scroll |
| `Button` | Clickable with on_click, keyboard-activatable |
| `Checkbox` | Boolean toggle with label |
| `Dropdown` | Option selector with floating list |
| `InputField` | Single-line text entry |
| `ProgressBar` | Horizontal or vertical fill bar |
| `RadioGroup` | Mutually exclusive option selector |
| `Slider` | Continuous value selector with keyboard support |
| `Label` | Single-line text display |
| `TextBlock` | Multi-line wrapped text |
| `Toast` | Auto-dismissing notification |
| `Tooltip` | Mouse-following context hint |

### Responsive layout
```python
from pygame_engine.layout import AnchorLayout, FlexRow, FlexColumn

layout = AnchorLayout()
layout.add(hud,  "top",          size=(400, 32), margin=8)
layout.add(btn,  "bottom_right", size=(120, 40), margin=16)
layout.apply(app.screen_rect)       # on_enter
layout.apply(pygame.Rect(0,0,w,h))  # on_resize

col = FlexColumn(spacing=4)
col.add(header,  fixed=60)
col.add(content, weight=1)
col.add(footer,  fixed=40)
col.layout(app.screen_rect)
```

---

## Camera

```python
from pygame_engine.camera import Camera

camera = Camera(app.config.width, app.config.height)
camera.set_world_bounds(tmap.world_rect)

# update:
camera.follow(player.rect.center, speed=6, dt=dt)
camera.update(dt)

# render:
screen_rect = camera.world_rect_to_screen(entity.rect)
surface.blit(entity.image, screen_rect)

# shake:
camera.add_trauma(0.6)

# mouse picking:
world_pos = camera.screen_to_world(pygame.mouse.get_pos())
```

---

## Tilemap

```python
from pygame_engine.tilemap import Tilemap, Tileset, TileLayer

tileset = Tileset.from_file(Path("assets/tiles.png"), 16, 16)
ground  = TileLayer("ground",    [[0,1,0],[2,0,2]])
walls   = TileLayer("collision", [[-1,3,-1],[3,3,3]])
tmap    = Tilemap(tileset, 16, 16, layers=[ground, walls])
tmap.set_collision_layer("collision")

tmap.render(surface, camera)
if tmap.collides_rect(player.rect):
    for tile in tmap.get_colliding_tiles(player.rect):
        resolve_overlap(player, tile)
```

---

## Dialogue

```python
from pygame_engine.dialogue import DialogueBox, DialogueRunner, DialogueScript

script = DialogueScript({"start": {"speaker": "NPC", "text": "Hello!", "next": "end"},
                          "end": {"text": ""}})
runner = DialogueRunner(script)
runner.on_complete = lambda: app.scene_manager.pop()
box    = DialogueBox(rect, runner, on_advance=lambda: runner.advance())
runner.start()

# each frame: box.update(dt); box.render(surface)
```

---

## Pathfinding

```python
from pygame_engine.pathfinding import ObstacleGrid, Pathfinder

grid   = ObstacleGrid.from_tilemap(tmap, collision_layer="walls")
finder = Pathfinder(grid, diagonal=True)
path   = finder.find((2, 3), (15, 10))   # [(col,row), ...]
waypoints = [tmap.tile_to_world(c, r) for c, r in path]
```

---

## Animation state machine

```python
from pygame_engine.animation import AnimationStateMachine

sm = AnimationStateMachine(player.animator)
sm.add_state("idle", default=True)
sm.add_state("run")
sm.add_transition("idle", "run",  lambda p: abs(p["vx"]) > 10)
sm.add_transition("run",  "idle", lambda p: abs(p["vx"]) <= 10)
sm.add_transition("*",    "dead", lambda p: p["hp"] <= 0, priority=10)

# each frame:
sm.update(dt, params={"vx": vx, "hp": hp})
```

---

## Positional audio

```python
from pygame_engine.audio.positional import PositionalAudio

pos = PositionalAudio(max_distance=600)
pos.set_listener(player.rect.centerx, player.rect.centery)
pos.play(explosion_sfx, enemy.rect.centerx, enemy.rect.centery)

src = pos.create_source(fire_sfx, loop=True, world_x=tx, world_y=ty)
src.start(pos)
src.update(pos)   # each frame
```

---

## 2D Lighting

```python
from pygame_engine.lighting import Light, LightingSystem

lights = LightingSystem(ambient=(10, 15, 30), darkness=0.9)
torch  = lights.add(Light(world_x=400, world_y=300,
                           radius=180, colour=(255,180,80), flicker=0.15))

# render order: world → lights.render(surface, camera) → UI
lights.update(dt)
lights.render(surface, camera)
```

---

## Sprite atlas

```python
from pygame_engine.atlas import AtlasPacker, SpriteAtlas

packer = AtlasPacker(max_size=2048)
packer.add("player", player_surf).add("coin", coin_surf)
atlas  = packer.build()
atlas.blit(screen, "player", dest=(x, y))

# save/load
packer.save(Path("assets/ui.atlas.png"), Path("assets/ui.atlas.json"))
atlas = app.assets.atlas("ui.atlas.png", "ui.atlas.json")
```

---

## Localisation

```python
from pygame_engine.locale import LocaleStore

store = LocaleStore(fallback_locale="en")
store.load_file(Path("assets/locale/en.json"), locale="en")
store.load_file(Path("assets/locale/fr.json"), locale="fr")
store.set_locale("en")

label.text = store.t("menu.start")
label.text = store.t("hud.score", value=42)
label.text = store.t("item.apple", count=3)  # plural form

# Hot-swap language at runtime
store.set_locale("fr")
store.available_locales   # ['en', 'fr']
```

In the game template, the `game.locale` module wraps this with a
module-level `t()` shorthand — see `game/locale/__init__.py`.

---

## Crash logging

```python
from pygame_engine.debug.crash_log import crash_guard
with crash_guard(Path("crash.log")):
    app.run(MainMenuScene(app))
```

---

## Audio

```python
app.audio.play_music(app.assets.asset_root / "music" / "theme.ogg")
app.audio.play_sfx(app.assets.sound("click.wav"))
app.audio.master_volume = 0.8
app.audio.toggle_mute()
```

---

## Animation

```python
from pygame_engine.animation import Tween
from pygame_engine.animation.easing import ease_out_back

slide = Tween(start=-300, end=0, duration=0.4,
              easing=ease_out_back, auto_start=True)
slide.update(dt)
panel.rect.x = int(slide.value)
```

---

## Events

```python
from pygame_engine.events import bus
bus.on("player.damaged", hud.on_player_damaged)
bus.once("tutorial.first_kill", show_tip)
bus.emit("player.damaged", amount=30, source="spike")
```

---

## File-driven theming

```python
from pathlib import Path
from pygame_engine.theme.loader import theme_from_file, reload_theme_file
from pygame_engine.theme.runtime import set_theme

# Load at startup
set_theme(theme_from_file(Path('assets/theme.json')))

# Hot-reload during development (press a key, or on file-watch)
reload_theme_file(Path('assets/theme.json'))
```

The JSON file is a partial override — only keys you want to change:

```json
{
    "colours": {"bg_base": [20, 20, 28]},
    "button":  {"normal": {"bg": [50, 85, 165], "radius": 6}}
}
```

---

## Rich text

```python
from pygame_engine.ui.text.rich_label import RichLabel

lbl = RichLabel(
    rect=pygame.Rect(x, y, w, h),
    text='[b]Score:[/b] [color=#ffd700]1 234[/color] pts',
)
lbl.render(surface)
```

Supported tags: `[b]bold[/b]`, `[i]italic[/i]`, `[color=#rrggbb]text[/color]`, `[size=N]text[/size]`.
Tags may be nested. Unknown tags render as literal text.

---

## Persistence

```python
from pygame_engine.persistence import SaveManager
from pathlib import Path

sm = SaveManager(save_dir=Path("saves"), game_id="my_game")

# Save arbitrary payload
sm.save("slot1", {"level": 3, "hp": 80, "items": ["sword"]})

# Load
data    = sm.load("slot1")
payload = data["payload"]

# Manage slots
sm.exists("slot1")  # True
sm.delete("slot1")
sm.list_slots()     # list of slot metadata dicts
```

---

## Particles

```python
from pygame_engine.particles.presets import (
    explosion, sparkle, smoke, fire_emitter, trail, hit_effect
)

# One-shot burst (call burst() then update/render each frame)
fx = explosion(mx, my)
fx.burst(40)

# Continuous emitter
fire = fire_emitter(x, y, rate=30)
fire.start()
fire.x, fire.y = player.rect.centerx, player.rect.bottom
fire.update(dt)
fire.render(surface)        # or fire.render_fast(surface)
fire.particle_count         # live particle count
fire.is_empty               # True when all particles dead
```

---

## State

```python
from pygame_engine.state import Observable
from pygame_engine.state.runtime_flags import flags

# Observable — fires callbacks on value change
score = Observable(0)
score.subscribe(lambda val: hud.set_score(val))
score.value = 100     # fires callback immediately
score.value           # 100

# RuntimeFlags — named boolean engine switches
flags.show_overlay = True   # F1 debug info panel
flags.show_console = True   # F3 log panel
flags.show_rects   = True   # widget bounding boxes
flags.toggle("show_fps")    # toggle by name
flags.reset()              # all back to False
flags.as_dict()            # {'debug': False, ...}
```

---

## Input remapping

```python
inp = app.input_manager

# Remap at runtime
inp.remap(actions.JUMP, pygame.K_z)
inp.remap_controller(actions.CONFIRM, button=0)

# Query current binding
key = inp.get_key_for_action(actions.CONFIRM)   # int or None
btn = inp.get_button_for_action(actions.CONFIRM)

# Human-readable names (for settings UI)
from pygame_engine.input.bindings import key_name, controller_button_name
key_name(pygame.K_RETURN)      # 'Enter'
controller_button_name(0)      # 'A / Cross'

# Serialise / restore / reset
saved = inp.bindings_to_dict()
inp.bindings_from_dict(saved)
inp.reset_to_defaults()
```

---

## Haptic feedback

```python
# Rumble all connected controllers
inp.rumble(low=0.3, high=0.8, duration_ms=200)

# Rumble a specific controller
inp.rumble(low=0.5, high=0.5, duration_ms=300, joystick_id=0)

# Stop immediately
inp.stop_rumble()
```

---

## Rules for game projects

1. Use engine primitives first — build custom only when needed.
2. Keep gameplay logic out of engine packages.
3. Game scenes, models, and systems live in your game repo.
4. If a pattern appears across multiple projects, only then consider moving it to the engine.
5. Update engine docs when engine contracts change.
========================================================================================================================