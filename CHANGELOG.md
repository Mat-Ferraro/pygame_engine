# Changelog

All notable changes to `pygame_engine` are recorded here.

---

## [1.3.0] — Phase 13: Theming & Rich Text

### Added
- `theme/loader.py` — `theme_from_file(path)`, `reload_theme_file(path)`, `theme_to_dict(theme)` — JSON partial theme overrides merged over defaults
- `ui/text/rich_label.py` — `RichLabel` widget with BBCode-style markup: `[b]`, `[i]`, `[color=#rrggbb]`, `[size=N]`, nestable tags
- `parse_markup()` — standalone parser returning styled span list
- `assets/theme.json` — starter theme override file for the repo root
- `game_template/assets/theme.json` — starter override for game projects
- `tests/test_theme_loader.py` — 30 tests
- `tests/test_rich_label.py` — 28 tests
- `docs/theme_system.md`, `docs/rich_text.md`

---

## [1.2.0] — Phase 12: Input & Controllers

### Added
- `InputManager.remap(action, key)` / `remap_controller(action, button)` — runtime key remapping
- `InputManager.bindings_to_dict()` / `bindings_from_dict()` — serialise bindings for persistence
- `InputManager.reset_to_defaults()` — restore default bindings
- `InputManager.rumble(low, high, duration_ms)` / `stop_rumble()` — haptic feedback
- `ControllerConfig` — dead zone, axis indices, threshold configuration
- Controller hot-plug via `JOYDEVICEADDED` events
- Axis→action mapping (left stick and D-pad → `NAV_*` actions)
- `key_name()` / `controller_button_name()` — human-readable names for UI
- `DEFAULT_CONTROLLER_BINDINGS` — A/Cross=CONFIRM, B/Circle=CANCEL, Start=PAUSE
- Settings scene Controls tab with live remapping and Apply/Discard workflow
- `tests/test_input_manager.py` — expanded to 67 tests (remapping, controller, haptic)
- `docs/input_system.md`

---

## [1.1.0] — Phase 11: Game AI & Systems

### Added
- `pathfinding/` — `ObstacleGrid`, `Pathfinder` — A* with 4/8-dir movement, corner prevention, `from_tilemap()`
- `lighting/` — `LightingSystem`, `Light` — dark overlay, radial gradients, flicker, camera-aware
- `audio/positional.py` — `PositionalAudio`, `PositionalSource` — distance falloff, stereo panning
- `animation/state_machine.py` — `AnimationStateMachine` — states, transitions, conditions, priority, any-state, callbacks
- `tests/test_pathfinding.py`, `test_lighting.py`, `test_positional_audio.py`, `test_animation_state_machine.py`
- `docs/pathfinding.md`, `docs/lighting.md`, `docs/positional_audio.md`, `docs/animation_state_machine.md`

---

## [1.0.0] — Phase 10: Polish & Utilities

### Added
- Screen manager — `on_resize()` hook, `set_resolution()`, `set_fullscreen()`, `toggle_fullscreen()`
- Responsive layout — `FlexRow`, `FlexColumn`, `AnchorLayout`
- Sprite atlas — `AtlasPacker`, `SpriteAtlas` — shelf packing, blit by name, save/load
- Localisation — `LocaleStore` — key lookup, plural forms, format substitution, hot-swap
- Crash logging — `crash_guard`, `install_crash_handler`

---

## [0.9.0] — Phase 9: Game Systems

### Added
- `Camera` — follow, zoom, screen shake, world bounds, visibility culling
- `Tilemap` — `Tileset`, `TileLayer`, multi-layer rendering, collision queries
- `Dialogue` — `DialogueScript`, `DialogueRunner`, `DialogueBox` with typewriter
- UI controls — `Slider`, `Checkbox`, `RadioGroup`

---

## [0.8.0] — Phase 8: Game Template & Polish

### Added
- Game template skeleton with `main.py`, scenes, locale, save system wired
- `EventBus` — wildcard subscriptions, one-shot handlers, broken-handler isolation
- Particle system — `Emitter` with 6 presets (explosion, sparkle, smoke, fire, trail, hit)
- Nine-slice panel rendering
- Focus management — Tab/Shift+Tab traversal
- `Dropdown` widget

---

## [0.7.0] — Phase 7: Stability & Expansion

### Added
- `DebugOverlay` (F1), `DebugConsole` (F3), `Inspector`, `debug_log`, `crash_log`
- `SaveManager` — atomic writes, dataclass serializers, migration pipeline
- `Observable[T]`, `RuntimeFlags`
- `Toast`, `Tooltip`, `InputField`, `ProgressBar`, `RadioGroup`, `Scrollable`
- `FadeTransition`, `SlideTransition`, `CrossfadeTransition`

---

## [0.1.0–0.6.0] — Phases 1–6: Foundations

### Added
- `Application`, `AppConfig` — main loop, delta-time, window management
- `Scene`, `SceneManager`, `SceneStack` — stack-based scene flow
- UI widgets — `Button`, `Label`, `TextBlock`, `Panel`, `Stack`
- Layout — `row`, `column`, `grid`, `anchor`
- Theme system — design tokens → defaults → runtime
- Action-based input — `InputManager`, `actions.py`, `bindings.py`
- `AssetLoader` — lazy-cached images, fonts, sounds
- `AudioManager` — music, SFX, volume, mute
- Animation — `Tween` (30 easings), `SpriteAnimation`, `AnimationPlayer`
- `EventBus` foundations
- `README.md`, `using_pygame_engine.md`, full test suite foundations
