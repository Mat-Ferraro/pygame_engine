# pygame_engine — Logging Standards

**Version:** 2.0-design
**Authority:** Supplements CODING_STANDARDS.md and ERROR_MESSAGE_STANDARDS.md

This document defines when and how to log in pygame_engine and in games
built with it. Consistent logging makes debugging faster and keeps the
output readable. Inconsistent logging produces noise that developers
learn to ignore — which defeats the purpose entirely.

---

## 1. The Two Output Systems

### debug_log — Structured Engine Logging

`pygame_engine.devtools.debug_log` is the engine's structured log. It
stores entries with level, tag, message, and timestamp. Entries are
viewable in the debug console (F3) and filterable by level and tag.
It does not write to stdout by default.

Use `debug_log` for:
- Any logging in `pygame_engine/` — always
- Game code logging that developers need to filter or review later
- Warnings and errors that should persist in the log panel

```python
from pygame_engine.devtools import debug_log

debug_log.log("Scene entered.", tag="management_scene")
debug_log.warn("Roster at capacity.", tag="guild_system")
debug_log.error("Save slot corrupted.", tag="save_manager")
```

### print() — Temporary Development Output

`print()` writes directly to stdout. Use it only during active
development when you need to see something immediately and `debug_log`
would require opening the debug console.

`print()` is never acceptable in `pygame_engine/`. It is a temporary
tool in game code, not a permanent output mechanism.

**Before committing any code:** remove all `print()` calls.
A linter rule flags `print()` in `pygame_engine/` as an error.
A linter warning flags it in game code.

---

## 2. Log Levels

### log() — Informational

Normal operation. Something happened that is worth knowing but is not
a problem. Developers reading the log expect to see these.

```python
debug_log.log("AudioManager initialised — 4 buses created.", tag="audio")
debug_log.log(f"Scene '{scene.__class__.__name__}' entered.", tag="scene_manager")
debug_log.log(f"Save slot '{slot}' written.", tag="save_manager")
```

Use `log()` sparingly. If every frame produces a log entry, the log
becomes useless. Log transitions and significant state changes — not
steady-state operation.

### warn() — Unexpected but Handled

Something unexpected happened but the system handled it with a
reasonable fallback. The developer should know. The game continues.

```python
debug_log.warn(
    f"Optional asset not found: {path!r}. Using placeholder.",
    tag="asset_manager"
)
debug_log.warn(
    f"Observable subscriber count ({count}) unusually high. "
    f"Check for subscription leaks.",
    tag="observable"
)
```

### error() — Incorrect Behaviour

Something went wrong that will affect behaviour. The game did not crash
(it would have raised if it were a developer error), but the result is
wrong in some way.

```python
debug_log.error(
    f"Layout file schema version {version} is newer than engine "
    f"version {ENGINE_VERSION}. Some properties may be ignored.",
    tag="layout_loader"
)
debug_log.error(
    f"Scene render() raised: {exception}. "
    f"ErrorScene is now active.",
    tag="application"
)
```

---

## 3. Tags

Every log call must include a `tag` identifying the system that logged it.
Tags make filtering possible — a developer debugging the audio system
can filter to `tag="audio"` and see only audio messages.

### Tag Conventions

Use the module or system name in snake_case:

```python
tag="scene_manager"       # pygame_engine/scene/scene_manager.py
tag="observable"          # pygame_engine/state/observable.py
tag="asset_manager"       # pygame_engine/assets/
tag="audio"               # pygame_engine/audio/
tag="save_manager"        # pygame_engine/persistence/
tag="layout_loader"       # editor/layout_io.py
tag="management_scene"    # game/scenes/management_scene.py
tag="guild_system"        # game/systems/guild/
```

Use the same tag consistently throughout a system. Do not use different
tags in different files of the same system.

### Tag Discovery

Tags are not pre-registered — any string is valid. This means a
developer can add a tag and immediately filter by it. The downside is
typos produce unfilterable output. Use constants for tags in systems
that log frequently:

```python
# In pygame_engine/scene/scene_manager.py
_LOG_TAG = "scene_manager"

debug_log.log(f"Pushed {scene.__class__.__name__}.", tag=_LOG_TAG)
debug_log.warn(f"Stack depth {depth}.", tag=_LOG_TAG)
```

---

## 4. Never Log in render()

Logging inside `render()` runs at 60fps. At that volume, the log
becomes a flood that makes debugging impossible and impacts performance.

If you need to debug a render issue, use one of these patterns:

**Frame throttle — log once per second:**
```python
def render(self, surface: pygame.Surface) -> None:
    # Debug only — remove before committing
    if self._frame_count % 60 == 0:
        debug_log.log(f"Rect: {self.rect}", tag="my_widget")
    self._frame_count += 1
    ...
```

**Condition log — log only when the relevant condition changes:**
```python
def update(self, dt: float) -> None:
    was_visible = self._visible
    self._visible = self._compute_visibility()
    if self._visible != was_visible:
        debug_log.log(
            f"Visibility changed to {self._visible}.",
            tag="my_widget"
        )
```

Log the state change in `update()`, not the state value in `render()`.

---

## 5. Log Message Format

### Content

Log messages answer: **what happened, in what context, with what values.**

```python
# Good — what, context, values
debug_log.log(
    f"Scene '{scene.__class__.__name__}' pushed onto stack "
    f"(depth: {len(self._stack)}/{self._max_depth}).",
    tag="scene_manager"
)

# Bad — vague, no context
debug_log.log("Scene pushed.", tag="scene_manager")
```

### Style

- Complete sentences ending with a period
- Present tense for current state, past tense for events that completed
- Include relevant values using `!r` for strings, plain formatting for numbers
- Do not include the tag in the message — the tag field handles that

```python
# Correct
debug_log.log(f"Asset '{path}' loaded in {elapsed_ms:.1f}ms.", tag="assets")

# Wrong — tag duplicated in message
debug_log.log(f"[assets] Asset '{path}' loaded.", tag="assets")

# Wrong — no context
debug_log.log("Asset loaded.", tag="assets")
```

### Length

Log messages should be one or two sentences. If you need more, the
situation warrants a warning or error level, not a longer message.

---

## 6. Development vs Production

In development mode (`app.mode == "development"`):
- All log levels are recorded and displayed
- Warnings appear in the debug console
- Errors trigger the ErrorScene with full details

In production mode (`app.mode == "production"`):
- `log()` and `warn()` are still recorded but not displayed to players
- `error()` triggers the ErrorScene with the game-configured message
- Stack traces are never shown to players

Do not suppress logging in production code paths — suppress display.
The structured log is still valuable for crash reporting and analytics
even when not shown to players.

Development-only log calls should be gated:
```python
if app.mode == "development":
    debug_log.log(
        f"Widget '{self.widget_id}' rebuilt cache "
        f"({len(lines)} lines, {elapsed_ms:.1f}ms).",
        tag="text_block"
    )
```

---

## 7. What Not to Log

**Personal data or file paths with usernames:**
```python
# Wrong — path exposes username on Windows
debug_log.log(f"Saving to C:\\Users\\alice\\AppData\\...", tag="save")

# Correct — relative or anonymised
debug_log.log(f"Saving to slot '{slot}'.", tag="save")
```

**Sensitive values:**
```python
# Never log API keys, passwords, or tokens — even in development
```

**Purely internal implementation state that adds no debugging value:**
```python
# Wrong — the developer does not need to know the internal dict size
debug_log.log(f"_registry has {len(self._registry)} entries.", tag="editor")

# Correct — log meaningful state
debug_log.log(f"Registry loaded: {len(self._registry)} scenes registered.", tag="editor")
```

**Every call to a frequently-called method:**
```python
# Wrong — this fires 60 times per second
def update(self, dt: float) -> None:
    debug_log.log("Update called.", tag="my_scene")  # never do this
```

---

## 8. Game Code Logging

Game code logging follows the same rules with slightly lower strictness:

- `debug_log` is preferred over `print()` for anything that should
  persist or be filterable
- `print()` is acceptable during active development — remove before
  the feature is considered complete
- Tags use the system or scene name: `"management_scene"`, `"campaign"`
- Log business logic events that are useful for debugging game state:
  hero hired, task dispatched, upgrade purchased

```python
# Good game code logging
debug_log.log(
    f"Hero '{hero.name}' hired at cost {cost}g. "
    f"Gold remaining: {self._state.gold}g.",
    tag="management_scene"
)

# Acceptable during development — remove before commit
print(f"DEBUG: hero.training_points = {hero.training_points}")
```