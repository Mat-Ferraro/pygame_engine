`pygame_engine` is a lightweight reusable pygame-ce framework for 2D games.

It provides: application loop, scene flow, UI toolkit, layout helpers,
theme system, input abstraction, assets, audio, animation, particles,
camera, tilemap, dialogue, pathfinding, lighting, localisation, and debug tools.

It does **not** provide: genre-specific gameplay logic, 3D rendering,
physics simulation, networking, or a visual editor.

---

## Project Direction

### Core goals
- Keep the public API understandable.
- Favour composition over inheritance.
- Separate rendering, input, layout, state, persistence, and scene flow.
- Make common pygame tasks easier without hiding pygame completely.
- Support good debug tooling without making it mandatory.

### Non-goals
- No game-specific hero, combat, inventory, or campaign logic.
- No giant `core/` catch-all package.
- No premature plugin ecosystem.
- No 3D rendering, physics engine, or networking.

---

## Repository Layout

```
pygame_engine/              ← repo root
├── docs/                   ← architecture and system documentation
├── examples/               ← 12 runnable usage examples
├── game_template/          ← copy-and-start skeleton for new projects
├── tests/                  ← 1100+ automated tests (38 files)
│   └── conftest.py
├── pygame_engine/          ← the importable Python package
│   ├── animation/          ← Tween, SpriteAnimation, AnimationPlayer, StateMachine
│   ├── app/                ← Application, AppConfig
│   ├── assets/             ← AssetLoader, SpriteLoader, FontCache
│   ├── atlas/              ← AtlasPacker, SpriteAtlas
│   ├── audio/              ← AudioManager, PositionalAudio
│   ├── camera/             ← Camera
│   ├── debug/              ← DebugOverlay, DebugConsole, Inspector, crash_log
│   ├── dialogue/           ← DialogueScript, DialogueRunner, DialogueBox
│   ├── events/             ← EventBus, Signal
│   ├── graphics/           ← draw helpers, nine-slice, sprite renderer
│   ├── input/              ← InputManager, actions, bindings
│   ├── layout/             ← anchor, row, column, grid, FlexRow, AnchorLayout
│   ├── lighting/           ← LightingSystem, Light
│   ├── locale/             ← LocaleStore
│   ├── particles/          ← Emitter, presets
│   ├── pathfinding/        ← ObstacleGrid, Pathfinder
│   ├── persistence/        ← SaveManager, storage, serializers, migrations
│   ├── scene/              ← Scene, SceneManager, SceneStack, transitions
│   ├── state/              ← Observable, RuntimeFlags
│   ├── theme/              ← tokens, defaults, runtime
│   ├── tilemap/            ← Tileset, TileLayer, Tilemap
│   ├── ui/                 ← 15 widgets, focus, containers
│   └── utils/              ← mathx, colors, rects, timers
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

---

## Package Responsibilities

### `app/`
Application startup and runtime. `Application` owns the main loop,
`AppConfig` holds configuration. Provides `set_resolution()`,
`set_fullscreen()`, `toggle_fullscreen()`, `screen_rect`.

### `scene/`
Scene contracts, stack management, and transitions.
- `scene.py` — `Scene` base with `on_enter/exit/pause/resume/resize`
- `scene_manager.py` — push/pop/replace, transitions, `notify_resize()`
- `transitions.py` — `FadeTransition`, `SlideTransition`, `CrossfadeTransition`

### `ui/`
15 reusable widgets:
- `base/` — `Widget`, focus ring
- `containers/` — `Panel`, `Stack`, `Scrollable` (open-Dropdown priority routing)
- `controls/` — `Button`, `Checkbox`, `Dropdown`, `InputField`, `ProgressBar`, `RadioGroup`, `Slider`
- `feedback/` — `Toast`, `Tooltip`
- `text/` — `Label`, `TextBlock`

### `layout/`
- Stateless: `anchor`, `row`, `column`, `grid`
- Stateful/responsive: `FlexRow`, `FlexColumn`, `AnchorLayout`

### `camera/`
`Camera` — world/screen conversion, smooth follow, screen shake, zoom, world bounds clamping, visibility culling.

### `tilemap/`
`Tileset`, `TileLayer`, `Tilemap` — multi-layer tile rendering, camera culling, collision queries.

### `dialogue/`
`DialogueScript`, `DialogueRunner`, `DialogueBox` — validated script format, pure-state-machine runner, typewriter widget.

### `pathfinding/`
`ObstacleGrid`, `Pathfinder` — A* with 4/8-dir movement, corner prevention, Tilemap integration.

### `lighting/`
`LightingSystem`, `Light` — dark overlay with radial gradient cutouts, flicker, camera-aware.

### `animation/`
- `Tween` — single-value animator, 30 easing functions
- `SpriteAnimation`, `AnimationPlayer` — frame-based sprite animation
- `AnimationStateMachine` — condition-driven state/transition machine

### `audio/`
- `AudioManager` — music, SFX, volume, mute
- `PositionalAudio`, `PositionalSource` — distance falloff, stereo panning

### `assets/`
`AssetLoader` — lazy cached images, spritesheets, fonts, sounds, atlas loading.

### `atlas/`
`AtlasPacker`, `SpriteAtlas` — shelf-packing, blit by name, save/load PNG+JSON.

### `locale/`
`LocaleStore` — JSON locale files, `t("key")` lookup, pluralisation, hot-swap.

### `particles/`
`Emitter` with 6 presets — explosion, sparkle, smoke, fire, trail, hit_effect.

### `persistence/`
`SaveManager`, atomic file writes, dataclass serializers, migration pipeline.

### `events/`
`EventBus` — wildcard subscriptions, one-shot handlers, broken-handler isolation. Module-level `bus` singleton.

### `debug/`
`DebugOverlay` (F1), `DebugConsole` (F3), `Inspector` (F2), `debug_log`, `crash_log`.

### `state/`
`Observable[T]`, `RuntimeFlags` — named boolean engine flags.

### `theme/`
Design tokens, `Theme` dataclass, `get_theme()`/`set_theme()`.
File-driven theming: `theme_from_file()`, `reload_theme_file()`, `theme_to_dict()`.

### `graphics/`
Draw helpers, nine-slice panels, sprite renderer, surface utilities.

### `input/`
`InputManager` — per-frame press/held/released, action queries, mouse, wheel.

### `utils/`
`mathx`, `colors`, `rects`, `timers` — small generic helpers.

---

## Current Implementation Status

All planned phases complete. 1033+ tests across 38 files.

- Phases 1–8: Runtime, UI, layout, theme, assets, audio, animation, particles, persistence, debug, EventBus, transitions, game template
- Phase 9: Camera, Tilemap, Dialogue, Slider/Checkbox/RadioGroup
- Phase 10: Screen manager (on_resize, set_resolution, set_fullscreen), Responsive layout, Sprite atlas, Localisation, Crash logging
- Phase 11: Pathfinding (A*), Animation state machine, Positional audio, 2D lighting
- Phase 12: Key remapping, controller/joystick support, binding persistence
- Phase 13: File-driven JSON theming with live reload, RichLabel rich text widget
  New tests: test_theme_loader.py (30 tests), test_rich_label.py (28 tests)

---

## Architectural Rules

1. Keep framework code generic — no game-specific logic.
2. Favour composition over deep inheritance.
3. Separate concerns: scenes → flow, widgets → UI, layout → positioning.
4. Expose a clean public API — top-level imports feel intentional.
5. Keep pygame visible — reduce boilerplate, don't hide the library.
6. No feature is complete until code, tests, examples, and docs all agree.
========================================================================================================================