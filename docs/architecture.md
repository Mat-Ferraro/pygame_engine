# Architecture

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
- pub/sub event bus

It does **not** aim to be a genre-specific gameplay engine.

---

## Project Direction

The framework should stay generic enough to support multiple future games while
still being practical to build with.

### Core goals
- Keep the public API understandable.
- Favor composition over inheritance.
- Separate rendering, input, layout, state, persistence, and scene flow.
- Make common pygame tasks easier without hiding pygame completely.
- Prefer proven reusable abstractions over speculative abstraction.
- Support good debug tooling without making debug systems mandatory to core
  runtime behavior.

### Non-goals
- No game-specific hero, combat, inventory, campaign, or economy logic.
- No giant `core/` catch-all package.
- No premature plugin ecosystem.
- No advanced fully general layout engine.

---

## Accepted Architecture Decisions

The following decisions are currently accepted:

- The engine is a **lightweight framework**, not a genre engine.
- The runtime model is **stack-based** for scenes.
- Clean public imports are preferred:
  ```python
  from pygame_engine.ui import Button
  from pygame_engine.scene import Scene, FadeTransition
  ```
- Scene and widget `handle_event` methods should return `bool`.
- Scenes may optionally own a `root_widget`.
- Base widgets should not automatically manage children.
- Layout uses assigned rects and simple helpers.
- Theme values are resolved through a stable runtime theme interface.
- Asset loading is lazy + cached and fails loudly during development.
- Persistence infrastructure belongs in the engine; save schema meaning belongs
  in the game.
- Engine state remains engine-level only.
- Typing is moderate but intentional.
- Scenes receive `Application` directly as a constructor argument.
- `Scene.render()` calls `overlay_render()` as a second pass for floating UI.

For the full condensed list, see `accepted_decisions.md`.

---

## Repository Layout

```
pygame_engine/              ← repo root
├── docs/                   ← all architecture and design documentation
├── examples/               ← runnable usage examples (manual smoke tests)
├── game_template/          ← copy-and-start skeleton for new game projects
├── tests/                  ← automated test suite (669+ tests)
│   └── conftest.py         ← shared pytest fixtures (headless pygame init)
├── pygame_engine/          ← the importable Python package
│   ├── __init__.py
│   ├── animation/
│   ├── app/
│   ├── assets/
│   ├── audio/
│   ├── debug/
│   ├── events/
│   ├── graphics/
│   ├── input/
│   ├── layout/
│   ├── particles/
│   ├── persistence/
│   ├── scene/
│   ├── state/
│   ├── theme/
│   ├── ui/
│   └── utils/
├── main.py                 ← development entry point
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

`docs/`, `examples/`, `tests/`, and `game_template/` live at the repo root,
not inside the importable package. This keeps the installable package tree clean.

---

## Package Responsibilities

### `app/`
Application startup and runtime orchestration.
- `application.py`: main app object and main loop
- `config.py`: runtime configuration values

### `scene/`
Scene contracts, scene flow, and transitions.
- `scene.py`: base scene contract with `render()` + `overlay_render()` pass
- `scene_manager.py`: scene orchestration with optional transition support
- `scene_stack.py`: layered scenes and overlays
- `transitions.py`: `FadeTransition`, `SlideTransition`, `CrossfadeTransition`

### `ui/`
Reusable UI primitives.
- `base/`: foundational widget contracts (`Widget`, `focusable`, focus ring)
- `containers/`: `Panel`, `Stack`, `Scrollable`
- `controls/`: `Button`, `Dropdown`, `InputField`, `ProgressBar`
- `feedback/`: `Toast`, `Tooltip`
- `text/`: `Label`, `TextBlock`
- `focus.py`: `FocusManager` mixin for Tab/Shift+Tab traversal

### `layout/`
Generic layout math and layout helpers.
- `row.py`, `column.py`, `grid.py`, `anchor.py`

### `theme/`
Visual design rules.
- `tokens.py`: raw design tokens
- `defaults.py`: default theme definitions
- `runtime.py`: active theme object and theme access

### `assets/`
Asset file access and caching.
- `asset_loader.py`: generic loading and cache entry points
- `sprite_loader.py`: image/sprite-specific load helpers
- `fonts.py`, `sounds.py`, `paths.py`: focused helpers by asset type

### `graphics/`
Rendering helpers.
- `draw_utils.py`: shared draw helpers
- `sprite_renderer.py`: sprite drawing with flip/alpha/rotation/scale
- `surfaces.py`: surface helpers
- `nine_slice.py`: scalable panel/image helpers (`draw_nine_slice`, `NineSlicePanel`)

### `input/`
Input abstraction.
- `actions.py`: action names/constants including `CONSOLE_TOGGLE`
- `bindings.py`: default key-to-action bindings (F1/F2/F3 for debug)
- `input_manager.py`: current input state and action queries

### `animation/`
Time-based animation helpers.
- `tween.py`: single-value animator with 30 easing functions
- `easing.py`: all Robert Penner easing families
- `animator.py`: `SpriteAnimation`, `AnimationPlayer`

### `particles/`
Reusable particle systems.
- `particle.py`: lightweight particle data container
- `emitter.py`: continuous + burst emission, physics, alpha/fast render
- `presets.py`: `explosion`, `sparkle`, `smoke`, `fire_emitter`, `trail`, `hit_effect`

### `persistence/`
Reusable save/load infrastructure.
- `save_manager.py`: top-level save/load orchestration
- `storage.py`: safe file read/write, atomic writes, `.bak` backups
- `serializers.py`: dataclass to/from dict, safe coercion helpers
- `migrations.py`: version upgrade pipeline

Accepted boundary:
- the engine handles persistence infrastructure
- the game handles save payload schema and game-state meaning

### `state/`
Small shared state helpers.
- `observable.py` — reactive value wrapper with subscriber callbacks
- `runtime_flags.py` — named boolean engine flags (`debug`, `show_fps`,
  `show_rects`, `show_overlay`, `show_console`) with module-level singleton

### `events/`
Pub/sub event bus for loose coupling between game systems.
- `event_bus.py` — `EventBus` with wildcard patterns, one-shot subscriptions,
  broken-handler isolation, module-level `bus` singleton
- `signals.py` — typed `Signal` wrapper around a specific event

### `debug/`
Development and inspection tools.
- `debug_log.py`: centralised log with level/tag filtering
- `overlay.py`: `DebugOverlay` — FPS, scene info, active flags (F1, `show_overlay`)
- `console.py`: `DebugConsole` — on-screen log tail (F3, `show_console`)
- `inspector.py`: `Inspector` — scene/widget tree dump to debug log (F2)

### `utils/`
Truly generic, low-level helpers only.
- `colors.py`: `lerp_color`, `brighten`, `hex_to_rgb`, `hsv_to_rgb`
- `mathx.py`: `clamp`, `lerp`, `remap`, `smoothstep`, `angle_to_vec`, `approach`
- `rects.py`: `inset`, `snap_to_grid`, `clamp_inside`, `split_horizontal`
- `timers.py`: `Timer`, `Cooldown`

---

## Persistence Boundary

The engine handles persistence infrastructure; games own the schema.

### Engine responsibilities
- save slot organisation
- file path resolution
- safe read/write behavior
- metadata structure, version fields
- migration hooks/infrastructure
- generic serializer helpers
- corruption detection support

### Game responsibilities
- what data gets saved
- the meaning of the save schema
- reconstruction of game state
- project-specific validation and migration logic

---

## Architectural Rules

1. **Keep framework code generic.** If a module only makes sense for one future game, it does not belong in `pygame_engine`.
2. **Favor composition.** Build larger UI pieces from smaller widgets and containers instead of deep inheritance trees.
3. **Separate concerns.** Scenes → flow. Widgets → local UI. Layout → positioning. Graphics → drawing. Assets → loading. Persistence → save/load. State → small shared runtime state.
4. **Keep modules narrowly scoped.** Avoid turning broad names into junk drawers.
5. **Expose a clean public API.** Top-level imports should feel intentional and stable.
6. **Keep pygame visible.** Reduce boilerplate without completely obscuring how pygame works.
7. **No feature is complete until code, tests, examples, and docs all agree.**

---

## Current Implementation Status

All planned systems are implemented. See `roadmap.md` for the complete inventory.

Key milestones reached:
- Full runtime spine: Application, Scene, SceneManager, SceneStack, transitions
- Complete UI toolkit: 12 widget types with focus traversal and overlay render pass
- Animation: Tween (30 easings), SpriteAnimation, AnimationPlayer
- Assets, Audio, Persistence (with migrations), Particles, EventBus
- Debug tools: overlay, console, inspector, debug log (all flag-gated)
- Game template: immediately runnable skeleton with working settings scene

---

## Decision Log Relationship

- `accepted_decisions.md` — current concise rule set
- `decision_log.md` — historical architecture choices
- Individual system docs — detailed behavior and contract notes
