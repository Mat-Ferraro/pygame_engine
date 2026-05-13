# Debug Tools

## Purpose

The debug package provides development-time visibility into runtime behavior.

Its role is to help engine and game developers inspect:
- frame timing and FPS
- current scene state and stack depth
- widget layout/bounds
- log output and events
- runtime flags and toggles

Debug tools remain optional runtime layers — they do not affect normal
runtime behavior when disabled.

---

## Accepted Core Decisions

- Debug tools are important and well supported
- They remain optional runtime layers, not mandatory core logic
- Debug activation is explicit via `AppConfig.debug` or `RuntimeFlags`
- Debug input is action-driven (F1/F2/F3), not hidden hardcoded keys
- Debug tools self-check their own flags — callers render them unconditionally

---

## Current Debug Modules

| Module | Role |
|---|---|
| `debug_log.py` | Centralised log with level/tag filtering, capped history |
| `overlay.py` | On-screen panel: FPS, frametime, scene name, active flags |
| `console.py` | On-screen tail of the debug log |
| `inspector.py` | Dumps scene stack and widget tree to the debug log |

---

## Activation

### Via AppConfig
```python
config = AppConfig(debug=True)   # enables all debug subsystems
```

This calls `flags.enable_debug_all()` during startup, which sets:
- `flags.debug = True`
- `flags.show_fps = True`
- `flags.show_rects = True`
- `flags.show_overlay = True`
- `flags.show_console = True`

### Via RuntimeFlags at runtime
```python
from pygame_engine.state.runtime_flags import flags
flags.show_overlay = True   # enable overlay only
flags.show_console = False  # keep console off
```

### Via keyboard (default bindings)
| Key | Action | Effect |
|---|---|---|
| F1 | `DEBUG_TOGGLE` | Toggles `flags.show_overlay` |
| F2 | `INSPECTOR_TOGGLE` | Dumps scene/widget tree to debug log |
| F3 | `CONSOLE_TOGGLE` | Toggles `flags.show_console` |

---

## RuntimeFlags

```python
from pygame_engine.state.runtime_flags import flags

flags.debug        # master switch — True when debug mode active
flags.show_fps     # show FPS in overlay
flags.show_rects   # draw widget/scene bounding rects
flags.show_overlay # show the debug overlay panel (F1)
flags.show_console # show the debug console log panel (F3)
```

**Note:** `show_overlay` and `show_console` are separate flags. Toggling
F1 does not affect the console; toggling F3 does not affect the overlay.

---

## Debug Overlay (`overlay.py`)

Draws a semi-transparent panel in the top-left corner showing:
- FPS and frame time
- Current scene name and stack depth
- Active RuntimeFlags

Controlled by `flags.show_overlay`. Toggle with F1.

```python
# Application calls this unconditionally each frame:
self._debug_overlay.render(self._display_surface, self._clock, self._scene_manager)
# DebugOverlay.render() returns immediately if flags.show_overlay is False.
```

---

## Debug Console (`console.py`)

Draws a semi-transparent panel at the bottom of the screen showing the
most recent debug log entries (up to 12 lines, colour-coded by level).

Display-only in v1 — not interactive (no command input).

Controlled by `flags.show_console`. Toggle with F3.

```python
# Application calls this unconditionally each frame:
self._debug_console.render(self._display_surface)
# DebugConsole.render() returns immediately if flags.show_console is False.
```

---

## Inspector (`inspector.py`)

Dumps the current scene stack and widget tree to the debug log when triggered.

```python
# Triggered by F2 (INSPECTOR_TOGGLE) in Application._handle_event()
from pygame_engine.debug.inspector import Inspector
Inspector().dump(scene_manager)
```

Output appears in the on-screen console and in the debug log history.

---

## Debug Log (`debug_log.py`)

Centralised log with level/tag filtering and a capped entry history.

```python
from pygame_engine.debug.debug_log import log, warn, error

log("Player spawned at (100, 200)", tag="game")
warn("Asset not found: missing.png", tag="assets")
error("Scene push failed", tag="engine")

# Read entries (newest first):
entries = get_entries(limit=20, level=LogLevel.WARN, tag="game")
```

---

## Usage from Game Code

```python
from pygame_engine.debug.debug_log import log

class CombatSystem:
    def apply_damage(self, amount):
        log(f"Damage applied: {amount}", tag="combat")
        ...
```

---

## Design Principles

1. Debug tools self-check their own flags — callers never need `if flags.debug:`.
2. Debug tools must always render on top of everything — they are rendered by
   `Application._loop` after scene rendering, not as scene widgets.
3. Debug code should not leak into clean runtime contracts.
4. Logs go through `debug_log`, not scattered `print()` calls.
5. Inspector reads state; it never owns or mutates state.

---

## Rules for Future Development

1. Keep debug tools optional — disable means zero cost.
2. Keep them layered on top of normal runtime behavior.
3. Keep logs centralised.
4. Prefer read-only inspection behavior where possible.
5. Any new debug toggle gets its own `RuntimeFlags` attribute and a bound action.
