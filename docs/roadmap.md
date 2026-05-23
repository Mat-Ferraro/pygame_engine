> **Note on Phase Numbering**
> This document tracks the original development phases (v1.x, Phases 1–13)
> and the subsequent v2.0 infrastructure phases (Phase A, Phase B).
> Phase numbering in `IMPLEMENTATION_ORDER.md` uses a different scheme for
> the v2.0 design work. These are separate numbering schemes.

---

Defines the development path for `pygame_engine` and keeps development
intentional, preventing random feature drift.

---

## Current Status — v1.4.0 — Phases 1–13 + Phase A + Phase B Complete

| Phase | Status | Summary |
|-------|--------|---------|
| Phase 1 — Runtime Foundations    | ✅ Complete | Application, Scene, SceneManager, SceneStack, Widget |
| Phase 2 — Layout, Theme, Input   | ✅ Complete | row/column/grid/anchor, theme system, InputManager |
| Phase 3 — Core UI Toolkit        | ✅ Complete | Panel, Stack, Button, Label, TextBlock, Toast, Tooltip |
| Phase 4 — Graphics, Animation    | ✅ Complete | Tween, easing, SpriteAnimation, AnimationPlayer, draw helpers |
| Phase 5 — Assets, Audio          | ✅ Complete | AssetLoader, AudioManager, font/image/sound caching |
| Phase 6 — Public API Cleanup     | ✅ Complete | README, using guide, import audit, example polish |
| Phase 7 — Stability & Expansion  | ✅ Complete | Debug tools, persistence, state, extended UI, transitions |
| Phase 8 — Game Template & Polish | ✅ Complete | Template, EventBus, particles, nine-slice, focus, Dropdown |
| Phase 9 — Game Systems           | ✅ Complete | Slider, Checkbox, RadioGroup, Camera, Tilemap, Dialogue |
| Phase 10 — Polish & Utilities    | ✅ Complete | Screen manager, responsive layout, sprite atlas, localisation |
| Phase 11 — Game AI & Systems     | ✅ Complete | Pathfinding, animation state machine, positional audio, 2D lighting |
| Phase 12 — Input & Controllers   | ✅ Complete | Key remapping, controller support, binding persistence |
| Phase 13 — Theming & Rich Text   | ✅ Complete | File-driven JSON theming, live reload, RichLabel with markup |
| Phase A — Observable Upgrade     | ✅ Complete | Observable (old/new sig, weak refs, transactions), SubscriptionGroup, RenderContext, AppConfig mode/reduced_motion |
| Phase B — Engine Infrastructure  | ✅ Complete | TimeManager, extension hooks, GlobalFocusManager, widget_id/tab_index/focus_trap, AudioBus topology |

---

## Phase A — Observable Upgrade ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `Observable[T]` upgrade | ✅ Done | Subscriber signature `(old, new)`, weak refs via `WeakMethod`, `transaction()`, `set_silent()` |
| `SubscriptionGroup` | ✅ Done | `on()`, `add()`, `dispose()` — wired into `Scene.on_exit()` for auto-cleanup |
| `AppConfig.mode` | ✅ Done | `"development"` / `"production"` / `"testing"` — controls debug tools and error behaviour |
| `AppConfig.reduced_motion` | ✅ Done | Accessibility flag; scenes check `app.reduced_motion` before playing animations |
| `RenderContext` | ✅ Done | Frozen dataclass carrying per-frame theme snapshot; threaded through all `render(surface, ctx)` calls |

---

## Phase B — Engine Infrastructure ✅ Complete

### Phase B1 — TimeManager

| Item | Status | Notes |
|------|--------|-------|
| `TimeManager` class | ✅ Done | `time_scale`, `delta_time`, `unscaled_delta_time`, `time`, `unscaled_time`, `frame_count` |
| `time_scale: Observable[float]` | ✅ Done | Set to `0.0` to pause all game logic; `0.5` for slow-mo |
| `max_delta_time` | ✅ Done | Clamp guard against spiral-of-death after OS suspend / breakpoints |
| `register_fixed_step(callback, rate)` | ✅ Done | Fixed-rate callbacks driven by scaled time; pause at `time_scale=0` |
| `app.time` property | ✅ Done | Raises `RuntimeError` before `run()` is called |
| Tests | ✅ Done | `tests/test_time_manager.py` — 32 tests |
| Example | ✅ Done | `examples/example_time_manager.py` — pause, slow-mo, fixed-step demo |

### Phase B2 — Extension Hooks

| Item | Status | Notes |
|------|--------|-------|
| `add_hook(name, callback, priority)` | ✅ Done | Six hooks: `startup`, `shutdown`, `pre_update`, `post_update`, `pre_render`, `post_render` |
| `remove_hook(name, callback)` | ✅ Done | Returns `True` if found and removed |
| Priority ordering | ✅ Done | Higher number fires later; equal priority fires in registration order |
| Tests | ✅ Done | `tests/test_extension_hooks.py` — 20 tests |
| Example | ✅ Done | `examples/example_hooks.py` — FrameLogger + FpsBar overlay via hooks |

### Phase B3 — GlobalFocusManager

| Item | Status | Notes |
|------|--------|-------|
| `GlobalFocusManager` | ✅ Done | `set_focus`, `clear_focus`, `next_focus`, `prev_focus`, `set_candidates` |
| `render_focus_ring(surface)` | ✅ Done | 2px ring drawn as post-render pass by Application |
| `ui.focus.changed` bus event | ✅ Done | Emitted on every focus change; carries the newly focused widget |
| `app.focus` property | ✅ Done | Available before `run()` — no pygame dependency |
| `Widget.widget_id` | ✅ Done | Optional string identifier for tooling and tests |
| `Widget.tab_index` | ✅ Done | Explicit Tab ordering; `None` = document order |
| `Widget.focus_trap` | ✅ Done | Prevents Tab escaping a modal widget's subtree |
| Tests | ✅ Done | `tests/test_global_focus.py` — 32 tests |
| Example | ✅ Done | `examples/example_focus.py` — tab_index ordering, focus trap, bus events |

### Phase B4 — AudioBus Topology

| Item | Status | Notes |
|------|--------|-------|
| `AudioBus` class | ✅ Done | `volume: Observable[float]`, `muted: Observable[bool]`, `effective_volume` via parent chain |
| Built-in buses | ✅ Done | `master`, `music`, `sfx`, `ui` — wired as parent chain on `AudioManager` |
| `ui` bus | ✅ Done | `respects_time_scale=False` — UI sounds play during game pause |
| `create_bus(name, parent)` | ✅ Done | Register custom buses (cutscene, ambient, etc.) |
| `get_bus(name)` | ✅ Done | Retrieve any registered bus by name |
| `AudioManager.update(time_scale)` | ✅ Done | Propagates pause policy to all buses each frame |
| `play_sfx(..., bus="ui")` | ✅ Done | Route sounds through any named bus |
| Backward compatibility | ✅ Done | Flat API (`master_volume`, `muted`, etc.) preserved as shims |
| Tests | ✅ Done | `tests/test_audio_bus.py` — 57 tests; `tests/test_audio.py` — 38 tests |

---

## Phase 9 — Game Systems ✅ Complete

### Phase 9a — Widget Expansion

| Item | Status | Notes |
|------|--------|-------|
| `Slider` | ✅ Done | Track + thumb, value range, keyboard support, vertical mode |
| `Checkbox` | ✅ Done | Checked state, label, `on_change`, keyboard activation |
| `RadioGroup` | ✅ Done | Mutually exclusive options, keyboard navigation |
| `app.screen_rect` | ✅ Done | `pygame.Rect(0, 0, config.width, config.height)` property |

### Phase 9b — Camera

| Item | Status | Notes |
|------|--------|-------|
| `Camera` class | ✅ Done | World offset, zoom, `world_to_screen()`, `screen_to_world()` |
| Smooth follow | ✅ Done | `follow(target, speed)` with exponential-decay lerp |
| Screen shake | ✅ Done | Trauma-based shake with configurable decay |
| World bounds | ✅ Done | `set_world_bounds()` clamps camera to world rect |
| Visibility culling | ✅ Done | `is_visible(rect, margin)` for entity culling |

### Phase 9c — Tilemap

| Item | Status | Notes |
|------|--------|-------|
| `Tileset` class | ✅ Done | `from_surface()`, `from_file()`, margin/spacing support |
| `TileLayer` class | ✅ Done | Named 2D grid, get/set/fill, ragged-row validation |
| `Tilemap` class | ✅ Done | Multi-layer, world offset, pixel/tile coordinate conversion |
| Layer rendering | ✅ Done | Camera-culled with zoom; per-layer visibility toggle |
| Collision map | ✅ Done | `collides_rect()`, `get_colliding_tiles()`, `get_tile_at_world()` |
| Tiled `.tmx` support | ⬜ Optional | Requires `pytmx`; deferred until a real game needs it |

### Phase 9d — Dialogue

| Item | Status | Notes |
|------|--------|-------|
| `DialogueScript` | ✅ Done | Validated JSON-compatible dict format; branching, actions, choices |
| `DialogueRunner` | ✅ Done | Pure state machine; advance/select_choice/jump; callbacks |
| `DialogueBox` widget | ✅ Done | Speaker bar, typewriter effect, choice buttons, keyboard shortcuts |
| `DialogueScene` | ⬜ Optional | Could wrap box+runner in a scene overlay; defer until needed |

---

## Phase 10 — Polish & Utilities ✅ Complete

### Phase 10a — Screen Manager

| Item | Status | Notes |
|------|--------|-------|
| `app.screen_rect` property | ✅ Done | Returns `Rect(0, 0, config.width, config.height)`; reflects post-resize size |
| Resize event signal | ✅ Done | `bus.emit("window.resized", width, height)` fired from `Application._on_resize` |
| `SceneManager` resize notification | ✅ Done | `notify_resize(w, h)` calls `on_resize` on top-of-stack scene only |
| Layout rebuild hook | ✅ Done | `Scene.on_resize(width, height)` — override to rebuild layout rects |

### Phase 10b — Responsive Layout

| Item | Status | Notes |
|------|--------|-------|
| `FlexRow` | ✅ Done | Horizontal distribution with weights, fixed sizes, min/max, spacing, padding |
| `FlexColumn` | ✅ Done | Vertical distribution with the same options as FlexRow |
| `AnchorLayout` | ✅ Done | Pin widgets to screen edges; `apply(bounds)` in `on_resize()` |

### Phase 10c — Sprite Atlas

| Item | Status | Notes |
|------|--------|-------|
| `SpriteAtlas` class | ✅ Done | `blit()`, `get_rect()`, `get_surface()`, `has()`, `from_surfaces()`, `load()` |
| `AtlasPacker` | ✅ Done | Shelf-packing algorithm; `add()`, `build()`, `save()` with JSON metadata |
| `AssetLoader` integration | ✅ Done | `app.assets.atlas(image_path, meta_path)` loads a pre-built atlas |

### Phase 10d — Localisation

| Item | Status | Notes |
|------|--------|-------|
| `LocaleStore` | ✅ Done | `load_file()`, `load_dict()`, `t("key")` with fallback chain |
| Pluralisation | ✅ Done | `t("key", count=n)` — zero/one/other forms |
| Format substitution | ✅ Done | `t("hud.score", value=42)` → `"Score: 42"` |
| Locale switching | ✅ Done | `set_locale("fr")` hot-swaps; falls back to fallback locale |
| Nested key flattening | ✅ Done | `{"menu": {"start": "Go"}}` → `"menu.start"` |

---

## Phases 11–13 ✅ Complete

See earlier CHANGELOG entries for full detail. Summary:

| Phase | Summary |
|-------|---------|
| Phase 11 — Game AI & Systems | A* pathfinding, animation state machine, positional audio, 2D lighting |
| Phase 12 — Input & Controllers | Key remapping, controller/joystick, dead zones, haptic feedback, binding persistence |
| Phase 13 — Theming & Rich Text | File-driven JSON theming, live hot-reload, RichLabel BBCode markup |

---

## Deliberately Skipped

| Item | Decision | Reason |
|------|----------|--------|
| Built-in physics | Skip | Out of scope. Use pymunk as a game-level dependency. |
| Networking / multiplayer | Skip | Highly game-specific; enormous scope. |
| Scripting VM / Lua | Skip | Would double engine complexity for marginal benefit at this scale. |

---

## Guiding Rules

1. Build what every game needs, not what some games need.
2. No feature is complete until code, tests, examples, and docs all agree.
3. Game-specific concerns stay in game projects.
4. If the same pattern appears across multiple real games, only then move it into the engine.
5. Keep the public API understandable. New systems get their own package.
6. Physics, networking, and scripting stay out of scope.
