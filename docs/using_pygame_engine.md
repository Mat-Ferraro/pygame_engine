## What the engine provides vs what your game provides

| Engine | Your game |
|---|---|
| Application runtime and main loop | Gameplay rules and systems |
| Scene flow and stack management | Game-specific scenes |
| UI widget library (15 widgets) | Composite widgets (inventory, HUD panels) |
| Layout, theme, input abstraction | Game keybindings and theme overrides |
| Camera, Tilemap, Dialogue | Game-specific maps, scripts, and entities |
| Pathfinding, Lighting, Audio | Game AI, atmosphere, sound design |
| Animation state machine | Character-specific states and transitions |
| Asset loading and caching | Asset files and directory structure |
| Persistence with migrations | Save payload schema and game state meaning |
| Localisation | Translation strings |
| Crash reporting | Game-specific error context |

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
from game.locale import t, load_locales, set_locale

load_locales()
label.text = t("menu.start")
label.text = t("hud.score", value=42)
label.text = t("item.apple", count=3)
set_locale("fr")
```

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

## Rules for game projects

1. Use engine primitives first — build custom only when needed.
2. Keep gameplay logic out of engine packages.
3. Game scenes, models, and systems live in your game repo.
4. If a pattern appears across multiple projects, only then consider moving it to the engine.
5. Update engine docs when engine contracts change.