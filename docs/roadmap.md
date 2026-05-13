# Roadmap

## Purpose

Defines the planned development path for `pygame_engine` and keeps
development intentional, preventing random feature drift.

---

## Current Status

| Phase | Status | Summary |
|-------|--------|---------|
| Phase 1 — Runtime Foundations    | ✅ Complete | Application, Scene, SceneManager, SceneStack, Widget |
| Phase 2 — Layout, Theme, Input   | ✅ Complete | row/column/grid/anchor, theme system, InputManager |
| Phase 3 — Core UI Toolkit        | ✅ Complete | Panel, Stack, Button, Label, TextBlock, Toast, Tooltip |
| Phase 4 — Graphics, Animation    | ✅ Complete | Tween, easing, SpriteAnimation, AnimationPlayer, draw helpers |
| Phase 5 — Assets, Audio          | ✅ Complete | AssetLoader, AudioManager, font/image/sound caching |
| Phase 6 — Public API Cleanup     | ✅ Complete | README, using guide, import audit, example polish |
| Phase 7 — Stability & Expansion  | ✅ Complete | See below |
| Phase 8 — Game Template & Polish | 🔲 In progress | See below |

---

## Phase 1 — Runtime Foundations ✅

- `Application`, `AppConfig`
- `Scene`, `SceneManager`, `SceneStack`
- Base `Widget`
- Main loop, delta-time, event routing, lifecycle hooks

---

## Phase 2 — Layout, Theme, Input ✅

- `row`, `column`, `grid`, `anchor` layout helpers
- Theme system: tokens → defaults → runtime, swappable at any time
- `InputManager`, `actions`, `DEFAULT_BINDINGS`

---

## Phase 3 — Core UI Toolkit ✅

- `Panel`, `Stack` containers
- `Button`, `Label`, `TextBlock`
- `Toast`, `Tooltip` feedback widgets

---

## Phase 4 — Graphics and Animation ✅

- `Tween` with 30 easing functions (all Robert Penner families)
- `SpriteAnimation`, `AnimationPlayer` — frame-based sprite animation
- `draw_utils` — `draw_surface_style`, `draw_rect_bordered`, chevrons, lines
- `surfaces` — `make_alpha_surface`, `blit_alpha`, scale, crop
- `sprite_renderer` — `draw_sprite`, `draw_animation_frame`

---

## Phase 5 — Assets and Audio ✅

- `AssetLoader` — image, spritesheet, font, sound loading with lazy caching
- `PathResolver` — centralised path resolution with folder conventions
- `AudioManager` — music streaming, SFX channels, volume controls, mute
- Placeholder surfaces for missing images in debug mode

---

## Phase 6 — Public API Cleanup ✅

- `README.md` — complete rewrite with quick-start, import reference
- `using_pygame_engine.md` — practical guide for building games
- Public import audit — all `__init__.py` files complete and consistent
- `example_app.py` — updated to showcase Tween, easing, theme, input

---

## Phase 7 — Stability and Expansion ✅

All planned Phase 7 items have been completed.

### Completed in this phase

**Debug tools**
- `debug_log` — centralised log with level/tag filtering, capped history
- `RuntimeFlags` — named boolean flags (`debug`, `show_fps`, `show_rects`, `show_overlay`)
- `DebugOverlay` — FPS/frametime, scene name, stack depth, active flags
- `DebugConsole` — on-screen log tail (bottom of screen)
- `Inspector` — scene stack and widget tree dump to debug log
- F1 toggles overlay, F2 dumps inspector

**Extended UI widgets**
- `Dropdown` — *(in progress, Phase 8)*
- `ProgressBar` — horizontal/vertical fill bar, value clamped to [0,1]
- `Scrollable` — clipping viewport with mouse-wheel scroll, scrollbar thumb
- `InputField` — single-line text entry, cursor, placeholder, password mode
- `Stack` — fixed: now properly follows base Widget contract
- `TextBlock` — multi-line wrapped text with caching

**Scene transitions**
- `FadeTransition` — fade through a solid colour (two-phase)
- `SlideTransition` — slide in from any edge (left/right/up/down)
- `CrossfadeTransition` — dissolve between scenes
- `SceneManager` extended with `push_with`, `replace_with`, `pop_with`

**Animation**
- `SpriteAnimation` — immutable frame data with uniform/per-frame durations
- `AnimationPlayer` — named animation registry, loop, ping-pong, on_finish

**Input**
- `InputField` provides text input mode via pygame TEXTINPUT events

**Persistence**
- `storage.py` — atomic writes, `.bak` backups, corrupt save detection
- `serializers.py` — dataclass to/from dict, safe type coercion helpers
- `migrations.py` — version pipeline with decorator-based handler registration
- `SaveManager` — slot management, game_id validation, envelope wrapping

**State**
- `Observable[T]` — reactive value wrapper with subscribe/unsubscribe
- `RuntimeFlags` — named engine boolean flags with module-level singleton

**Cleanup**
- Removed `events/` package (empty stubs, `Observable` covers the need)
- Removed `state/state_store.py` (no concrete use case, dumping-ground risk)
- 330+ passing tests across 19 test files

---

## Phase 8 — Game Template and Polish 🔲 In progress

### Completed

- **Game project template** (`game_template/`) — immediately runnable skeleton:
  - `main.py` — fully wired entry point with config, bindings, theme hooks
  - `game/actions.py` — engine + game-specific action constants
  - `game/scenes/main_menu.py` — working main menu with transitions
  - `game/scenes/game_scene.py` — stub gameplay scene ready to fill in
  - `game/scenes/pause_scene.py` — pause overlay with correct blocking policy
  - `game/scenes/settings_scene.py` — settings overlay with back navigation
  - `game/models/`, `game/systems/`, `game/ui/` — documented stub packages
  - `README.md` — comprehensive "how to use this template" guide

### Remaining

**`Dropdown` widget** — the last planned UI control. Settings screens and
option selectors need it. Complex (floating list, z-ordering, click-outside
to close) but well-defined.

**Nine-slice rendering** — `graphics/nine_slice.py` stub. Needed for scalable
dialog boxes and speech bubbles without distortion. Straightforward to
implement once Dropdown is done.

**Focus traversal** — Tab key navigation between widgets. The `focused` flag
exists on every widget. Container-level traversal logic needs implementing.
Important for keyboard-navigable settings and forms.

**Particle system** — `particles/` (emitter, particle, presets) are all empty
stubs. Every game wants hit effects, explosions, weather. Deferred until a
real game pulls on it.

**EventBus** — ✅ now implemented. See `docs/event_model.md`.
`Signal` typed wrapper also available in `events/signals.py`.

---

## Out of Scope — Physics

`pygame_engine` will not include a physics engine.

Physics is deep, specialised, and genre-specific. A platformer, top-down
RPG, and billiards game each need fundamentally different physics behaviour.

**Recommended approach:** Use **pymunk** (the standard pygame physics library,
wrapping Chipmunk) as a direct game-project dependency, not an engine one.

---

## Ongoing rules

- Keep framework code generic — no game-specific logic in the engine
- Keep docs updated when contracts or decisions change
- Add tests for all reusable deterministic logic
- Prefer small, stable contracts over rapid abstraction growth
- Only expand when a real game use case pulls on it
