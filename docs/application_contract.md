# Application Contract

## Purpose

`Application` is the top-level runtime owner for a project built on
`pygame_engine`. It bootstraps pygame, owns the main loop, coordinates the
high-level runtime, and exposes shared services to scenes.

The `Application` is one of the most stable contracts in the entire engine.

---

## Accepted Core Decisions

- `pygame_engine` is a lightweight framework, not a genre engine
- The scene runtime model is stack-based
- Debug tools are important but remain optional runtime layers
- Engine-level shared state stays limited to engine/runtime concerns
- Typing is moderate but intentional

---

## Responsibilities

`Application` is responsible for:

- Initialising and shutting down pygame
- Creating and owning the display surface/window
- Owning the master clock and producing delta-time each frame
- Driving the frame loop (event → update → render → present)
- Routing pygame events into the active scene flow
- Initialising and exposing shared runtime services
- Applying high-level configuration
- Integrating optional debug systems as non-blocking layers

It acts as the runtime shell of the engine.

---

## Non-Responsibilities

`Application` should **not**:

- Contain gameplay logic
- Contain scene-specific logic or widget-specific logic
- Act as a general-purpose global store or service locator

---

## Public Interface

```python
from pygame_engine.app import Application, AppConfig

config = AppConfig(title="My Game", width=1280, height=720, debug=False)
app    = Application(config)
app.run(MainMenuScene(app))   # single entry point — does everything
```

### Methods
- `run(initial_scene)` — the single public entry point; starts up, loops, shuts down
- `stop()` — signals the loop to exit cleanly after the current frame
- `set_theme(theme)` — replace the active theme

### Properties (all valid only after `run()` is called)
- `scene_manager` — the `SceneManager` instance
- `input_manager` — the `InputManager` instance
- `assets` — the `AssetLoader` instance
- `audio` — the `AudioManager` instance
- `theme` — the active `Theme` (equivalent to `get_theme()`)
- `config` — the `AppConfig` this app was created with
- `display_surface` — the main pygame display surface
- `clock` — the master pygame clock
- `is_running` — True while the main loop is active

---

## Lifecycle

### Construction (`__init__`)
Side-effect-free. Stores config only. Pygame is not touched here.

### Startup (`_startup`)
Called once by `run()` before the loop:
1. `pygame.init()`
2. Create display surface
3. Create clock
4. Set window caption
5. Initialise `InputManager`, `AssetLoader`, `AudioManager`
6. Reset `RuntimeFlags`; apply `config.debug` via `flags.enable_debug_all()`
7. Create `SceneManager` and push the initial scene

### Main Loop (`_loop`)
Runs every frame in this fixed order:
```
1.  Poll events
2.  Update input snapshot
3.  Route events to scene flow
4.  Update scene flow
5.  Clear back-buffer
6.  Render scene flow
7.  Render debug overlays (no-op when flags are off)
8.  Flip / present display
9.  Tick clock → compute dt for next frame
```

### Shutdown (`_shutdown`)
Called in a `finally` block — always runs:
1. Pop all scenes (calling `on_exit()` on each)
2. Shut down audio
3. Clear event bus (`bus.clear_all()`)
4. `pygame.quit()`

---

## Event Routing

`Application._handle_event()` routes events in priority order:

1. Application-level essentials (QUIT, window resize)
2. Scene flow via `SceneManager.handle_event()`
3. Global debug shortcuts:
   - F1 → `DEBUG_TOGGLE` → toggles `flags.show_overlay`
   - F2 → `INSPECTOR_TOGGLE` → dumps scene/widget tree to debug log
   - F3 → `CONSOLE_TOGGLE` → toggles `flags.show_console`

---

## Service Access from Scenes

Scenes receive `Application` directly as a constructor argument:

```python
class GameScene(Scene):
    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app

    def on_enter(self):
        frames = self._app.assets.spritesheet("player.png", 48, 48)
        self._app.audio.play_music(...)
        self._app.scene_manager.push_with(PauseScene(self._app), FadeTransition())
```

See `accepted_decisions.md` Decision #23 for rationale.

---

## Configuration

`AppConfig` is a plain dataclass. All fields have sensible defaults:

```python
@dataclass
class AppConfig:
    title:      str   = "pygame_engine"
    width:      int   = 1280
    height:     int   = 720
    target_fps: int   = 60
    max_dt:     float = 0.1       # clamp guard — prevents huge dt spikes
    resizable:  bool  = False
    fullscreen: bool  = False
    vsync:      bool  = False
    asset_root: Path  = Path("assets")
    debug:      bool  = False     # enables all debug overlays
```

---

## Rules for Development

1. Keep `Application` small and predictable.
2. Do not let it absorb gameplay code.
3. Do not let it become a universal dependency container.
4. Keep frame order stable — document any change.
5. Treat it as core framework infrastructure, not an extension playground.

---

## Locked Implementation Decisions

### Single `run(initial_scene)` entry point
No separate `start()` / `run()` split. One call does everything. Construction
(`__init__`) is side-effect-free — pygame is not touched until `run()`.
Shutdown is guaranteed via a `finally` block.

### `Application` owns all services directly
`InputManager`, `AssetLoader`, `AudioManager` are all constructed by
`Application._startup()`. No external injection or plugin system.

### Rendering always targets the main display surface
The display surface is created once in `_startup()` and re-created only on
window resize. Off-screen render targets are not supported.

### Scenes receive Application directly
How much of `Application`'s services scenes access is now settled: scenes
take `Application` as a constructor argument and use `self._app`. See
`accepted_decisions.md` Decision #23.

### Back-buffer always cleared to black
`self._display_surface.fill((0, 0, 0))` runs each frame before scene render.
Scenes control their own background colour in their `render()` method.

### `bus.clear_all()` on shutdown
The module-level event bus is cleared on application shutdown to prevent stale
handler references surviving between sessions or test runs.
