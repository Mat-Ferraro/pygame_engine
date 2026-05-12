# pygame_engine Architecture

## Purpose

`pygame_engine` is a lightweight reusable pygame framework.

It exists to provide:
- a clean application loop
- scene flow
- reusable UI primitives
- layout helpers
- theme support
- input abstraction
- asset, persistence, audio, and debug support
- animation and particle helpers

It does **not** aim to be a genre-specific gameplay engine in version one.

---

## Project Direction

The framework should stay generic enough to support multiple future games while still being practical to build with.

### Core goals
- Keep the public API understandable.
- Favor composition over inheritance.
- Separate rendering, input, layout, state, persistence, and scene flow.
- Make common pygame tasks easier without hiding pygame completely.
- Prefer proven reusable abstractions over speculative abstraction.
- Support good debug tooling without making debug systems mandatory to core runtime behavior.

### Non-goals
- No game-specific hero, combat, inventory, campaign, or economy logic.
- No giant `core/` catch-all package.
- No premature plugin ecosystem.
- No advanced fully general layout engine in version one.

---

## Accepted Architecture Decisions

The following decisions are currently accepted:

- The engine is a **lightweight framework**, not a genre engine.
- The runtime model is **stack-based** for scenes.
- Clean public imports are preferred:
  ```python
  from pygame_engine.ui import Button
  from pygame_engine.scene import Scene
  ```
- Scene and widget `handle_event` methods should return `bool`.
- Scenes may optionally own a `root_widget`.
- Base widgets should not automatically manage children.
- Layout in version one should use assigned rects and simple helpers.
- Theme values should be resolved through a stable runtime theme interface.
- Asset loading should be lazy + cached and fail loudly during development.
- Persistence infrastructure belongs in the engine, while save schema meaning belongs in the game.
- Engine state should remain engine-level only.
- Typing should be moderate but intentional.

For the full condensed list, see `accepted_decisions.md`.

---

## Current Package Structure

```text
pygame_engine/
  animation/
  app/
  assets/
  audio/
  debug/
  docs/
  events/
  examples/
  graphics/
  input/
  layout/
  particles/
  persistence/
  scene/
  state/
  tests/
  theme/
  ui/
  utils/
```

### Package responsibilities

#### `app/`
Application startup and runtime orchestration.
- `application.py`: main app object and main loop
- `config.py`: runtime configuration values

#### `scene/`
Scene contracts and scene flow.
- `scene.py`: base scene contract
- `scene_manager.py`: scene orchestration
- `scene_stack.py`: layered scenes and overlays
- `transitions.py`: transition helpers

#### `ui/`
Reusable UI primitives.
- `base/`: foundational widget contracts
- `containers/`: panel-like widgets and composition containers
- `controls/`: interactive controls like buttons and dropdowns
- `feedback/`: tooltips, toasts, and short-lived feedback widgets
- `text/`: label and text-display widgets

#### `layout/`
Generic layout math and layout helpers.
- row
- column
- grid
- anchor

#### `theme/`
Visual design rules.
- `tokens.py`: raw design tokens
- `defaults.py`: default theme definitions
- `runtime.py`: active theme object and theme access

#### `assets/`
Asset file access and caching.
- `asset_loader.py`: generic asset loading and cache entry points
- `sprite_loader.py`: image/sprite-specific load helpers
- `fonts.py`, `sounds.py`, `paths.py`: focused helpers by asset type

#### `graphics/`
Rendering helpers.
- `draw_utils.py`: shared draw helpers
- `sprite_renderer.py`: sprite drawing/render support
- `surfaces.py`: surface helpers
- `nine_slice.py`: scalable panel/image helpers

#### `input/`
Input abstraction.
- `actions.py`: action names
- `bindings.py`: default bindings
- `input_manager.py`: current input state and action queries

#### `animation/`
Time-based animation helpers.
- `tween.py`
- `easing.py`
- `animator.py`

#### `particles/`
Reusable particle systems.
- `particle.py`
- `emitter.py`
- `presets.py`

#### `persistence/`
Reusable save/load infrastructure.
- `save_manager.py`: top-level save/load orchestration
- `storage.py`: safe file read/write behavior
- `serializers.py`: generic serialization helpers
- `migrations.py`: migration infrastructure

Accepted boundary:
- the engine handles persistence infrastructure
- the game handles save payload schema and game-state meaning

#### `state/`
Small shared state helpers.
- `observable.py`
- `runtime_flags.py`
- `state_store.py`

#### `events/`
Loose coupling between subsystems.
- `signals.py`
- `event_bus.py`

#### `debug/`
Development and inspection tools.
- `console.py`
- `debug_log.py`
- `inspector.py`
- `overlay.py`

#### `utils/`
Truly generic, low-level helpers only.
- `colors.py`
- `mathx.py`
- `rects.py`
- `timers.py`

#### `examples/`
Human-facing usage examples and manual smoke tests.

#### `tests/`
Automated tests for reusable logic.

#### `docs/`
Project decisions and framework contracts.

---

## Persistence Boundary

Persistence is an engine-supported system, but it remains intentionally lightweight.

### Engine responsibilities
The engine may handle:
- save slot organization
- file path resolution
- safe read/write behavior
- metadata structure
- version fields
- migration hooks/infrastructure
- generic serializer helpers
- corruption detection support

### Game responsibilities
The game project should handle:
- what data gets saved
- the meaning of the save schema
- reconstruction of game state
- project-specific validation
- game-specific migration logic

This keeps `pygame_engine` generic while still providing real save/load infrastructure.

---

## Architectural Rules

### 1. Keep framework code generic
If a module only makes sense for one future game, it does not belong in `pygame_engine`.

### 2. Favor composition
Build larger UI pieces from smaller widgets and containers instead of deep inheritance trees.

### 3. Separate concerns
- scenes manage flow
- widgets manage local UI behavior
- layout manages positioning logic
- graphics manages drawing helpers
- assets manage file loading/caching
- persistence manages save/load infrastructure
- state manages small shared runtime state

### 4. Keep modules narrowly scoped
Avoid turning broad names like `asset_loader`, `draw_utils`, `state_store`, or `save_manager` into junk drawers.

### 5. Expose a clean public API
Top-level imports should feel intentional and stable.

### 6. Keep pygame visible
The framework should reduce boilerplate, not completely obscure how pygame works.

### 7. Design for future expansion without overbuilding
This especially applies to layout, theming, persistence, and higher-level engine features.

---

## Current Version One Boundary

Version one currently aims to provide:
- `Application`
- `Scene`
- `SceneManager`
- `SceneStack`
- `Widget`
- `Panel`
- `Button`
- `Label`
- `TextBlock`
- basic layout helpers
- theme runtime/defaults
- input manager/actions/bindings
- basic asset loading
- basic persistence infrastructure
- examples

---

## Next Implementation Priorities

The first contracts to define and stabilize are:
1. `Application`
2. `Scene`
3. `SceneManager` / `SceneStack`
4. `Widget`

These are the highest-leverage parts of the framework. If they are clean, the rest of the project can grow on top of them without major rework.

Persistence should be treated as supporting infrastructure and should not distract from the runtime spine.

---

## Decision Log Relationship

Use:
- `accepted_decisions.md` for the current concise rule set
- `decision_log.md` for historical architecture choices
- system docs for detailed behavior and contract notes
