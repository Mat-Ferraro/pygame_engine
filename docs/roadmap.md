## Purpose

Defines the development path for `pygame_engine` and keeps development
intentional, preventing random feature drift.

---

## Current Status — v1.0 Complete, Phase 9 Complete, Phase 10 Planned

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

---

## Phase 9 — Game Systems ✅ Complete

### Phase 9a — Widget Expansion ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `Slider` | ✅ Done | Track + thumb, value range, keyboard support, vertical mode |
| `Checkbox` | ✅ Done | Checked state, label, `on_change`, keyboard activation |
| `RadioGroup` | ✅ Done | Mutually exclusive options, keyboard navigation |
| `app.screen_rect` | ✅ Done | `pygame.Rect(0, 0, config.width, config.height)` property |

### Phase 9b — Camera ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `Camera` class | ✅ Done | World offset, zoom, `world_to_screen()`, `screen_to_world()` |
| Smooth follow | ✅ Done | `follow(target, speed)` with exponential-decay lerp |
| Screen shake | ✅ Done | Trauma-based shake with configurable decay |
| World bounds | ✅ Done | `set_world_bounds()` clamps camera to world rect |
| Visibility culling | ✅ Done | `is_visible(rect, margin)` for entity culling |

### Phase 9c — Tilemap ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `Tileset` class | ✅ Done | `from_surface()`, `from_file()`, margin/spacing support |
| `TileLayer` class | ✅ Done | Named 2D grid, get/set/fill, ragged-row validation |
| `Tilemap` class | ✅ Done | Multi-layer, world offset, pixel/tile coordinate conversion |
| Layer rendering | ✅ Done | Camera-culled with zoom; per-layer visibility toggle |
| Collision map | ✅ Done | `collides_rect()`, `get_colliding_tiles()`, `get_tile_at_world()` |
| Tiled `.tmx` support | ⬜ Optional | Requires `pytmx`; deferred until a real game needs it |

### Phase 9d — Dialogue ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `DialogueScript` | ✅ Done | Validated JSON-compatible dict format; branching, actions, choices |
| `DialogueRunner` | ✅ Done | Pure state machine; advance/select_choice/jump; callbacks |
| `DialogueBox` widget | ✅ Done | Speaker bar, typewriter effect, choice buttons, keyboard shortcuts |
| `DialogueScene` | ⬜ Optional | Could wrap box+runner in a scene overlay; defer until needed |

---

## Phase 10 — Polish & Utilities 🔄 Planned

These items were deferred from earlier phases and are now queued for
implementation. Each is scoped and ready to build.

### Phase 10a — Screen Manager ✅ Complete

Completes the "layout per scene size" work started with `app.screen_rect`.

| Item | Status | Notes |
|------|--------|-------|
| `app.screen_rect` property | ✅ Done | Returns `Rect(0, 0, config.width, config.height)`; reflects post-resize size |
| Resize event signal | ✅ Done | `bus.emit("window.resized", width, height)` fired from `Application._on_resize` |
| `SceneManager` resize notification | ✅ Done | `notify_resize(w, h)` calls `on_resize` on top-of-stack scene only |
| Layout rebuild hook | ✅ Done | `Scene.on_resize(width, height)` — override to rebuild layout rects |

### Phase 10b — Responsive Layout ✅ Complete

A lightweight anchor+flex hybrid — stateful helpers that recompute on resize.

| Item | Status | Notes |
|------|--------|-------|
| `FlexRow` | ✅ Done | Horizontal distribution with weights, fixed sizes, min/max, spacing, padding |
| `FlexColumn` | ✅ Done | Vertical distribution with the same options as FlexRow |
| `AnchorLayout` | ✅ Done | Pin widgets to screen edges; `apply(bounds)` in `on_resize()` |
| Integration with Screen Manager | ✅ Done | All three classes designed to be called from `Scene.on_resize()` |

### Phase 10c — Sprite Atlas ✅ Complete

Pre-bake many small images into one surface to reduce blit overhead.

| Item | Status | Notes |
|------|--------|-------|
| `SpriteAtlas` class | ✅ Done | `blit()`, `get_rect()`, `get_surface()`, `has()`, `from_surfaces()`, `load()` |
| `AtlasPacker` | ✅ Done | Shelf-packing algorithm; `add()`, `build()`, `save()` with JSON metadata |
| `AssetLoader` integration | ✅ Done | `app.assets.atlas(image_path, meta_path)` loads a pre-built atlas |

### Phase 10d — Localisation ✅ Complete

String key → translated string lookup. Engine-agnostic.

| Item | Status | Notes |
|------|--------|-------|
| `LocaleStore` | ✅ Done | `load_file()`, `load_dict()`, `t("key")` with fallback chain |
| Pluralisation | ✅ Done | `t("key", count=n)` — zero/one/other forms |
| Format substitution | ✅ Done | `t("hud.score", value=42)` → `"Score: 42"` |
| Locale switching | ✅ Done | `set_locale("fr")` hot-swaps; falls back to fallback locale |
| Nested key flattening | ✅ Done | `{"menu": {"start": "Go"}}` → `"menu.start"` |
| Game template integration | ✅ Done | `game/locale/en.json` + `game/locale/__init__.py` with `t()` shortcut |

---

## Phase 11 — Game AI & Systems ✅ Complete

### Phase 11a — Pathfinding ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `ObstacleGrid` | ✅ Done | 2D boolean grid; `from_tilemap()` factory; `set_obstacle()`, `fill()` |
| `Pathfinder` | ✅ Done | A* with 4-dir and 8-dir (diagonal) movement; corner-cutting prevention |

### Phase 11b — Animation State Machine ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `AnimationStateMachine` | ✅ Done | States, transitions, conditions, priority, any-state, on_enter/on_exit callbacks |

### Phase 11c — 2D Positional Audio ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `PositionalAudio` | ✅ Done | Distance falloff, stereo panning, configurable rolloff |
| `PositionalSource` | ✅ Done | Looping positioned sources with per-frame update |

### Phase 11d — 2D Lighting ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `Light` | ✅ Done | World-position light with radius, colour, intensity, flicker |
| `LightingSystem` | ✅ Done | Dark overlay with radial gradient cutouts; camera-aware |

---

## Phase 12 — Input & Controllers ✅ Complete

### Phase 12a — Key Remapping ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `InputManager.remap()` | ✅ Done | Rebind any action to a new key at runtime |
| `InputManager.remap_controller()` | ✅ Done | Rebind controller buttons |
| `get_key_for_action()` / `get_button_for_action()` | ✅ Done | Query current binding |
| `bindings_to_dict()` / `bindings_from_dict()` | ✅ Done | Serialise for persistence |
| `reset_to_defaults()` | ✅ Done | Restore default bindings |
| `key_name()` / `controller_button_name()` | ✅ Done | Human-readable names for UI |
| Settings scene Controls tab | ✅ Done | Live remapping UI with persistence |

### Phase 12b — Controller Support ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| Joystick detection | ✅ Done | Auto-detects on `JOYDEVICEADDED`; hot-plug support |
| Button → action mapping | ✅ Done | Same action strings as keyboard |
| Axis → action mapping | ✅ Done | Left stick and D-pad → NAV_* actions with threshold |
| Dead zone filtering | ✅ Done | Configurable via `ControllerConfig` |
| `ControllerConfig` | ✅ Done | Dead zone, axis indices, threshold |
| Raw axis access | ✅ Done | `get_axis(joy_id, axis)` for analogue movement |

---

## Phase 13 — Theming & Rich Text ✅ Complete

### Phase 13a — File-driven Theming ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `theme_from_file(path)` | ✅ Done | Load JSON theme override file; partial — only override what you need |
| `reload_theme_file(path)` | ✅ Done | Load and immediately activate — hot-reload during development |
| `theme_to_dict(theme)` | ✅ Done | Serialise active theme to JSON-compatible dict |
| JSON format | ✅ Done | Colours as `[r,g,b]`, all keys optional, deep merge over defaults |
| Sample `assets/theme.json` | ✅ Done | Starter file in game template |

### Phase 13b — Rich Text ✅ Complete

| Item | Status | Notes |
|------|--------|-------|
| `RichLabel` widget | ✅ Done | BBCode markup: `[b]`, `[i]`, `[color=#rrggbb]`, `[size=N]` |
| `parse_markup()` | ✅ Done | Standalone parser — returns list of styled spans |
| Font caching | ✅ Done | Per-instance font variant cache; no reallocation between frames |
| Graceful degradation | ✅ Done | Unknown tags rendered as literal text, never crash |

---

## Deliberately Skipped

These were evaluated and will not be built into the engine.

| Item | Decision | Reason |
|------|----------|--------|
| Built-in physics | Skip | Out of scope by accepted decision. Use pymunk as a game-level dependency. |
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