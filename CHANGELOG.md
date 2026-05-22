The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — Phase A: CHANGE-01 + CHANGE-07

### Added
- `pygame_engine/state/subscription_group.py` — new `SubscriptionGroup` class
  with `on()`, `add()`, `dispose()`, and `subscription_count`
- `pygame_engine/state/__init__.py` — `SubscriptionGroup` exported from
  `pygame_engine.state`
- `examples/example_observable.py` — interactive demo: weak refs, transactions,
  SubscriptionGroup, subscriber signature
- `tests/test_subscription_group.py` — full test suite for SubscriptionGroup
  including Scene integration tests

### Changed
- `pygame_engine/state/observable.py` — **CHANGE-01** Observable[T] upgrade:
  - Subscriber signature changed from `callback(new_value, old_value)` to
    `callback(old_value, new_value)` — **breaking change**
  - Bound method subscriptions held via `weakref.WeakMethod`; dead refs
    cleaned lazily on next notification (memory leak fix)
  - New `transaction()` context manager — batches changes, fires one event
    on exit with `(old_value, new_value)` where old is value at block entry
  - Nested transactions transparent (inner does not fire separately)
  - `listener_count` counts only live refs
  - `subscribe()` returns the listener as an unsubscription token
- `pygame_engine/scene/scene.py` — **CHANGE-07** SubscriptionGroup integration:
  - `Scene.__init__()` added; creates `self.subscriptions: SubscriptionGroup`
  - `Scene.on_exit()` calls `self.subscriptions.dispose()` automatically
  - Subclasses must call `super().__init__()` and `super().on_exit()`
  - Added `on_resize(width, height)` no-op lifecycle hook
- `tests/test_state.py` — all subscriber lambdas updated for `(old, new)`;
  new tests for weak refs, transactions, Hypothesis property-based tests
- `run_examples.py` — `example_observable` registered under Core
- `game_template/game/scenes/game_scene.py` — `on_exit` calls `super().on_exit()`;
  subscriptions usage pattern added as comment in `on_enter`

---

## [Unreleased] — Audit #3 Fixes

### Fixed
- `tilemap/tilemap.py` — added docstrings to `tileset` and `layer_names` properties
- `input/input_manager.py` — added docstring to `is_controller_button_down`
- `pyproject.toml` — pinned `pygame-ce==2.5.7` (exact per R19 and DEPENDENCY_POLICY.md)
- `pyproject.toml` — added `platformdirs>=4.0` as declared runtime dependency

### Changed
- `docs/CODEBASE_CHANGES.md` — removed duplicate C1 and C8 plain-text entries; new markdown versions kept
- `docs/accepted_decisions.md` — added notice pointing to DESIGN_SPEC.md and RESTRICTIONS.md
- `docs/NEW_STANDARDS_CHANGES.md` — added resolution status table for N1–N14

### Removed (from git tracking)
- `crash.log` — gitignored but was committed; removed with `git rm`
- `pygame_engine.egg-info/` — gitignored build artifact; removed with `git rm -r`

---

## [Unreleased] — Standards and Documentation

### Added
- `docs/DESIGN_SPEC.md` — comprehensive v2.0 architecture and design specification
- `docs/RESTRICTIONS.md` — 20 enforceable development restrictions with rationale
- `docs/CODING_STANDARDS.md` — docstring format, comment standards, naming conventions
- `docs/CODEBASE_CHANGES.md` — technical debt register with C1–C13 tracked changes
- `docs/IMPLEMENTATION_ORDER.md` — phased implementation plan for v2.0 features
- `docs/GIT_STANDARDS.md` — Conventional Commits format, branch strategy, fixup workflow
- `docs/REVIEW_CHECKLIST.md` — blocking/non-blocking review criteria, done definition
- `docs/IMPORT_STANDARDS.md` — four-group import ordering, TYPE_CHECKING guard, game layer dependency direction
- `docs/TYPE_ANNOTATION_STANDARDS.md` — annotation rules, overload patterns, type aliases
- `docs/LOGGING_STANDARDS.md` — debug_log usage, log levels, tag conventions
- `docs/PERFORMANCE_BUDGETS.md` — frame budget targets, exceeded-budget process
- `docs/ERROR_MESSAGE_STANDARDS.md` — three-question rule, warning message format
- `docs/DEPENDENCY_POLICY.md` — runtime/optional/dev dependency categories, pinning policy
- `docs/ACCESSIBILITY_STANDARDS.md` — keyboard navigation, colour contrast, reduced motion
- `docs/VERSIONING_GUIDE.md` — semantic versioning, release checklist, deprecation process
- `docs/SCENE_AUTHORING_GUIDE.md` — practical guide for writing scenes against the engine
- `docs/NEW_STANDARDS_CHANGES.md` — audit findings N1–N14 with required fixes
- `docs/AUDIT_MAY_2026.md` — first full codebase and documentation audit
- `docs/AUDIT_2_MAY_2026.md` — second audit confirming fix status
- Docstrings added to 192 → 80 public API members across 42 engine files

### Fixed
- `particles/emitter.py` — replaced `Union[X, Y]` with `X | Y` syntax (deprecated typing import removed)
- `persistence/migrations.py` — renamed `fn` parameter to `migration_fn` (banned abbreviation)
- `debug/inspector.py` — replaced `print(report)` with `return report`
- `dialogue/runner.py` — removed module-body `print()` calls from example lambdas
- `persistence/save_manager.py` — removed leftover debug `print()` call
- `theme/loader.py` — replaced `print(json.dumps(...))` with `return`
- `state/runtime_flags.py` — added `-> None` to `__init__` signature
- `ui/feedback/confirm_dialog.py` — added `-> None` to outer and inner `__init__` signatures
- `debug/crash_log.py` — added justification comments for intentional `print()` to stderr
- `animation/easing.py` — all 27 easing functions now have docstrings
- `input/input_manager.py` — 14 frequently-used query methods now documented
- `ui/controls/badge.py`, `int_stepper.py`, `list_view.py`, `scrollable.py` — docstrings added
- `ui/controls/key_value_panel.py`, `log_panel.py`, `progress_bar.py`, `input_field.py` — docstrings added
- `ui/text/label.py`, `rich_label.py`, `text_block.py` — `set_rect` docstrings added
- `dialogue/box.py`, `script.py` — `update`, `render`, and property docstrings added
- `lighting/lighting.py` — property and `render` docstrings added
- `audio/audio_manager.py`, `positional.py` — volume and property docstrings added
- `atlas/atlas.py` — `count` and `clear` docstrings added
- `scene/transitions.py` — `render` docstrings added to all concrete transition classes
- `layout/anchor_layout.py`, `flex.py` — `set_rect` and `item_count` docstrings added
- `locale/locale_store.py` — `has_locale` docstring added
- `pathfinding/pathfinder.py` — property docstrings added
- `tilemap/tilemap.py` — property docstrings added
- `utils/timers.py` — `duration` docstring added
- `theme/tokens.py` — class docstrings added to all six token classes
- `debug/debug_log.py` — `LogEntry` class docstring added
- `animation/animator.py`, `tween.py` — property docstrings added
- `tilemap/layer.py`, `tileset.py` — property docstrings added
- `camera/camera.py` — property docstrings added

### Changed
- `docs/naming_conventions.md` — marked SUPERSEDED, points to `CODING_STANDARDS.md`
- `docs/roadmap.md` — added phase numbering disambiguation note
- `docs/ARCHITECTURE.md` — added pointer to `DESIGN_SPEC.md` as authoritative reference
- `examples/example_phase14.py` — deleted; content lives in `examples/example_ui_widgets.py`

---

## [Unreleased]

### Infrastructure
- Established project structure: repo root contains `docs/`, `examples/`, `tests/`, and the `pygame_engine/` package
- Moved `docs/`, `examples/`, and `tests/` out of the importable package tree to repo root
- Added `CHANGELOG.md`
- Added `tests/conftest.py` with headless pygame fixture
- All source modules are stubs pending implementation

---

_Development is currently in the architecture and infrastructure phase._

### Added — Application spine
- `pygame_engine/app/config.py` — `AppConfig` dataclass (window, timing, display, paths, debug)
- `pygame_engine/app/application.py` — `Application` class with full contract-level signatures:
  - Side-effect-free `__init__`
  - Single `run(initial_scene)` entry point
  - `_startup` / `_loop` / `_shutdown` lifecycle
  - Fixed frame-loop order (poll → input → events → update → render → flip → dt)
  - `_handle_event` with priority routing stubs
  - `_compute_dt` with configurable clamping
  - `stop()`, `config`, `is_running`, `display_surface`, `clock` properties
- `pygame_engine/app/__init__.py` — exports `Application`, `AppConfig`
- Locked four Application open questions; recorded in `decision_log.md` and `application_contract.md`

### Added — Scene system
- `pygame_engine/scene/scene.py` — `Scene` base class with full lifecycle hooks and frame methods
- `pygame_engine/scene/scene_stack.py` — `SceneStack` with blocking-policy traversals (input/update/render)
- `pygame_engine/scene/scene_manager.py` — `SceneManager` with push/pop/replace/clear_and_push and lifecycle hook orchestration
- `pygame_engine/scene/transitions.py` — documented stub (deferred)
- `pygame_engine/scene/__init__.py` — exports `Scene`, `SceneManager`, `SceneStack`
- `pygame_engine/app/application.py` — wired `SceneManager`; `run()` now accepts `Scene`; shutdown pops all scenes cleanly; `scene_manager` property added

### Added — Widget base
- `pygame_engine/ui/base/widget.py` — `Widget` base class with rect, interaction state (visible, enabled, hovered, focused), frame methods, `set_rect`, `contains_point`, `is_interactive` property
- `pygame_engine/ui/base/__init__.py` — exports `Widget`
- `pygame_engine/ui/__init__.py` — clean public import surface; other widgets stubbed/commented until implemented
- `pygame_engine/scene/scene.py` — `root_widget` now typed as `Widget | None`; all three frame method TODOs resolved with real delegation calls
- Locked Widget open questions; recorded in `widget_contract.md` and `decision_log.md`

### Added — Spine example
- `examples/example_app.py` — minimal end-to-end example exercising the full chain: AppConfig → Application → SceneManager → ExampleScene → ColourBlock (Widget subclass)
- `main.py` — uncommented to run example_app by default

### Added — Input system
- `pygame_engine/input/actions.py` — canonical action string constants (NAV_UP/DOWN/LEFT/RIGHT, CONFIRM, CANCEL, PAUSE, DEBUG_TOGGLE, INSPECTOR_TOGGLE, CONSOLE_TOGGLE)
- `pygame_engine/input/bindings.py` — default key-to-action mapping (DEFAULT_BINDINGS)
- `pygame_engine/input/input_manager.py` — per-frame input state: keyboard (pressed/released/down), mouse (pos, delta, buttons, wheel), action queries, rebinding support
- `pygame_engine/input/__init__.py` — exports InputManager and actions module
- `pygame_engine/app/application.py` — InputManager wired in; `update(events)` called each frame; `input_manager` property added
- `examples/example_app.py` — ESC quit now uses `was_action_pressed(actions.CANCEL)` instead of raw key check

### Added — Layout helpers
- `pygame_engine/layout/_shared.py` — internal `Align` type and `_resolve_align()` helper
- `pygame_engine/layout/anchor.py` — `anchor()`: place a rect at a named point within bounds (9 anchor points, margin, offset)
- `pygame_engine/layout/row.py` — `row()`: distribute items horizontally with spacing, padding, vertical align
- `pygame_engine/layout/column.py` — `column()`: distribute items vertically with spacing, padding, horizontal align
- `pygame_engine/layout/grid.py` — `grid()`: uniform grid with spacing and padding, centred block
- `pygame_engine/layout/__init__.py` — exports `anchor`, `column`, `grid`, `row`
- `examples/example_app.py` — replaced manual rect math with `anchor(screen, (200, 120), "center")`

### Added — Button and Label widgets
- `pygame_engine/ui/text/label.py` — `Label`: single-line text widget, cached render surface, left/center/right alignment, dirty-flag invalidation on text/colour/rect change
- `pygame_engine/ui/text/__init__.py` — exports `Label`
- `pygame_engine/ui/controls/button.py` — `Button`: clickable widget with `on_click` callback, normal/hovered/pressed/disabled visual states, internal `Label` for text
- `pygame_engine/ui/controls/__init__.py` — exports `Button`
- `pygame_engine/ui/__init__.py` — now exports `Widget`, `Button`, `Label`
- `examples/example_buttons.py` — demonstrates Button, Label, column layout, disabled state, status updates, ESC via action system
- `main.py` — updated to run example_buttons by default

### Added — Theme system
- `pygame_engine/theme/tokens.py` — raw design tokens: `Colours`, `Spacing`, `Typography`, `Radii`, `Borders`, `Timing`
- `pygame_engine/theme/defaults.py` — `Theme` dataclass hierarchy: `SurfaceStyle`, `TextStyle`, `ButtonTheme`, `LabelTheme`, `PanelTheme`, `ColoursTheme`, `TypographyTheme`, `SpacingTheme`; `DEFAULT_THEME` instance
- `pygame_engine/theme/runtime.py` — `get_theme()`, `set_theme()`, `reset_theme()` module-level accessors
- `pygame_engine/theme/__init__.py` — public exports
- `pygame_engine/app/application.py` — `app.theme` property and `app.set_theme()` method added
- `pygame_engine/ui/text/label.py` — reads font size, colour, family from theme; `_UNSET` sentinel for explicit override detection
- `pygame_engine/ui/controls/button.py` — all colour constants replaced with `get_theme()` lookups; all states styled via `theme.button.*`
- `examples/example_buttons.py` — scene background uses `theme.colours.bg_base`

### Added — Panel container and utils
- `pygame_engine/ui/containers/panel.py` — `Panel`: child list, themed background/border, event routing (reverse order), update/render (forward order), optional clipping
- `pygame_engine/ui/containers/__init__.py` — exports `Panel`
- `pygame_engine/ui/__init__.py` — now exports `Widget`, `Panel`, `Button`, `Label`
- `pygame_engine/utils/timers.py` — `Timer` (countdown, progress, remaining) and `Cooldown` (auto-reset interval timer)
- `pygame_engine/utils/colors.py` — `lerp_color`, `lerp_color_alpha`, `brighten`, `with_alpha`, `hex_to_rgb`, `rgb_to_hex`, `hsv_to_rgb`
- `pygame_engine/utils/rects.py` — `rect_from_center`, `rect_from_corners`, `inset`, `inset_xy`, `snap_to_grid`, `clamp_inside`, `split_horizontal`, `split_vertical`
- `pygame_engine/utils/mathx.py` — `clamp`, `clamp01`, `remap`, `remap_clamped`, `lerp`, `lerp_clamped`, `smoothstep`, `smootherstep`, `angle_to_vec`, `vec_to_angle`, `approach`
- `pygame_engine/utils/__init__.py` — documents public import paths
- `examples/example_buttons.py` — updated to use `Panel` instead of `WidgetGroup` stand-in; buttons now inside a themed panel; all colours from theme

### Added — Toast and Tooltip feedback widgets
- `pygame_engine/ui/feedback/tooltip.py` — `Tooltip`: follows mouse, fade-in, screen-clamped, show()/hide() API
- `pygame_engine/ui/feedback/toast.py` — `Toast`: auto-dismiss with fade-in/hold/fade-out lifecycle, kind-based accent colour (info/success/warning/error), dismiss()
- `pygame_engine/ui/feedback/__init__.py` — exports `Toast`, `Tooltip`
- `pygame_engine/ui/__init__.py` — now exports full widget set: Widget, Panel, Stack, Button, Label, TextBlock, Toast, Tooltip
- `examples/example_feedback.py` — demonstrates all three toast kinds, tooltip on hover, ESC to dismiss toast or quit
- `main.py` — updated to run example_feedback by default

### Added — Animation system
- `pygame_engine/animation/easing.py` — 30 easing functions (linear, quad, cubic, quart, sine, expo, circ, back, elastic, bounce — in/out/in-out variants), `EASING_FUNCTIONS` registry, `get_easing(name)`
- `pygame_engine/animation/tween.py` — `Tween`: single-value float animator with easing, loop, ping-pong, start/stop/restart/complete/reverse
- `pygame_engine/animation/__init__.py` — exports `Tween`
- `tests/test_easing.py` — boundary conditions, monotonicity, overshoot behaviour, registry
- `tests/test_tween.py` — interpolation, easing applied, control methods, loop, ping-pong
- `docs/animation_system.md` — full animation system documentation

### Added — Graphics helpers
- `pygame_engine/graphics/draw_utils.py` — `draw_surface_style` (themed rect + border), `draw_rect_bordered`, `draw_horizontal_line`, `draw_vertical_line`, `draw_cross`, `draw_chevron`
- `pygame_engine/graphics/surfaces.py` — `make_alpha_surface`, `make_solid_surface`, `blit_alpha`, `blit_alpha_surface`, `scale_surface`, `crop_surface`
- `pygame_engine/graphics/__init__.py`

### Refactored — Widgets now use graphics helpers
- `pygame_engine/ui/containers/panel.py` — `_draw_background` uses `draw_surface_style`
- `pygame_engine/ui/controls/button.py` — render uses `draw_surface_style`
- `pygame_engine/ui/feedback/toast.py` — uses `make_alpha_surface`, `blit_alpha_surface`
- `pygame_engine/ui/feedback/tooltip.py` — uses `make_alpha_surface`, `blit_alpha_surface`

### Added — Asset system
- `pygame_engine/assets/paths.py` — `PathResolver`: resolves relative paths under asset root, with `font()`, `image()`, `sound()` subdirectory helpers
- `pygame_engine/assets/sprite_loader.py` — `SpriteLoader`: image loading/caching, spritesheet slicing, magenta placeholder in debug mode
- `pygame_engine/assets/fonts.py` — `FontCache`: file font and SysFont loading/caching by (path, size, bold, italic) key
- `pygame_engine/assets/sounds.py` — `SoundCache`: sound loading/caching, missing files log warning and return None
- `pygame_engine/assets/asset_loader.py` — `AssetLoader`: central entry point wrapping all three caches; `image()`, `spritesheet()`, `font()`, `sysfont()`, `sound()`, `clear_cache()`
- `pygame_engine/assets/__init__.py` — exports `AssetLoader`, `AssetNotFoundError`
- `pygame_engine/app/application.py` — `AssetLoader` wired in; `app.assets` property added
- `docs/asset_pipeline.md` — locked decisions documented including physics out-of-scope
- `docs/roadmap.md` — physics explicitly noted as out of scope with pymunk recommendation

### Added — Audio system
- `pygame_engine/audio/audio_manager.py` — `AudioManager`: music streaming (play/stop/pause/resume/fade), SFX playback, master/music/sfx volume controls, mute toggle, clean shutdown
- `pygame_engine/audio/__init__.py` — exports `AudioManager`
- `pygame_engine/app/application.py` — `AudioManager` wired in; `app.audio` property added; `audio.shutdown()` called in `_shutdown()`
- `docs/audio_system.md` — full audio system documentation

### Phase 6 — Public API Cleanup
- `README.md` — complete rewrite: quick-start example, full import reference, examples guide, documentation table
- `docs/using_pygame_engine.md` — practical usage guide: project structure, scenes, UI, input, theme, assets, audio, animation, timers
- `pygame_engine/__init__.py` — updated docstring listing all subpackage imports
- `pygame_engine/graphics/__init__.py` — now properly exports all helpers (was missing actual imports)
- `examples/example_app.py` — rewritten to showcase Tween + ease_out_back slide-in, pulsing animation, theme colours, action-based input
- `docs/roadmap.md` — complete rewrite with phase status table, Phase 7 expansion list, guiding rules

### Added — Persistence system
- `pygame_engine/persistence/storage.py` — `read`, `write` (atomic .tmp→rename + .bak), `delete`, `exists`, `list_saves`; `StorageError`, `SaveNotFoundError`, `CorruptSaveError`
- `pygame_engine/persistence/serializers.py` — `to_dict`, `from_dict` for dataclasses; `safe_int`, `safe_float`, `safe_bool`; `ensure_str_keys`
- `pygame_engine/persistence/migrations.py` — `MigrationRunner`: decorator-based handler registration, chained version upgrades, `needs_migration`
- `pygame_engine/persistence/save_manager.py` — `SaveManager`: save/load/delete/exists/list_slots, envelope wrapping, game_id validation, automatic migration on load
- `pygame_engine/persistence/__init__.py` — exports `SaveManager`, error classes
- `tests/test_persistence.py` — 34 tests covering storage, serializers, migrations, and SaveManager

### Added — State system
- `pygame_engine/state/observable.py` — `Observable[T]`: reactive value wrapper with subscribe/unsubscribe/clear_listeners, set_silent, equality-checked notifications
- `pygame_engine/state/runtime_flags.py` — `RuntimeFlags`: named boolean engine flags (debug, show_fps, show_rects, show_overlay), toggle(), reset(), enable_debug_all(), as_dict(); module-level `flags` singleton
- `pygame_engine/state/__init__.py` — exports `Observable`, `RuntimeFlags`, `flags`
- `pygame_engine/app/application.py` — resets `flags` on startup; enables all debug flags when `AppConfig.debug=True`
- `tests/test_state.py` — 23 tests covering Observable and RuntimeFlags

### Added — Debug tools
- `pygame_engine/debug/debug_log.py` — `log`, `warn`, `error`, `get_entries`, `clear`; capped history (200 entries), level and tag filtering
- `pygame_engine/debug/overlay.py` — `DebugOverlay`: FPS/frametime with colour coding, scene name and stack depth, active flags; self-checks `flags.show_overlay`
- `pygame_engine/debug/inspector.py` — `Inspector`: text-based scene stack and widget tree dump to debug_log; `format_scene_stack`, `format_widget_tree`, `format_flags`
- `pygame_engine/debug/console.py` — `DebugConsole`: on-screen log tail (8 most recent entries), level-coloured text, bottom of screen; display-only in v1
- `pygame_engine/debug/__init__.py` — exports `DebugOverlay`, `DebugConsole`, `Inspector`
- `pygame_engine/app/application.py` — overlay and console wired into `_loop`; F1 toggles `show_overlay`; F2 triggers inspector dump
- `tests/test_debug_log.py` — 11 tests covering log levels, tag/level filtering, limit, clear, timestamps

### Added — ProgressBar widget
- `pygame_engine/ui/controls/progress_bar.py` — `ProgressBar`: horizontal/vertical fill bar, value clamped to [0,1], optional fill/bg/radius overrides, theme-driven defaults
- `pygame_engine/ui/controls/__init__.py` — now exports `Button`, `ProgressBar`
- `pygame_engine/ui/__init__.py` — now exports `ProgressBar`
- `tests/test_progress_bar.py` — 13 tests covering value clamping, fill rect geometry for both directions, edge cases

### Added — Scrollable container
- `pygame_engine/ui/containers/scrollable.py` — `Scrollable`: clipping viewport with vertical mouse-wheel scrolling, offset-adjusted event routing to child, proportional scrollbar thumb, scroll_by/scroll_to_top/scroll_to_bottom API
- `pygame_engine/ui/containers/__init__.py` — now exports `Panel`, `Stack`, `Scrollable`
- `pygame_engine/ui/__init__.py` — now exports `Scrollable`
- `tests/test_scrollable.py` — 16 tests covering scroll clamping, max_scroll, wheel events, position offsetting, child routing

### Added — InputField widget
- `pygame_engine/ui/controls/input_field.py` — `InputField`: typing via TEXTINPUT events, backspace/delete, left/right/Home/End cursor, click-to-focus, placeholder, password masking, max_length, on_change/on_submit callbacks, blinking cursor
- `pygame_engine/ui/controls/__init__.py` — now exports `Button`, `InputField`, `ProgressBar`
- `pygame_engine/ui/__init__.py` — now exports `InputField`
- `tests/test_input_field.py` — 27 tests covering insertion, backspace, delete, cursor movement, callbacks, focus, placeholder, password, clear

### Added — Sprite animation
- `pygame_engine/animation/animator.py` — `SpriteAnimation`: immutable frame data with uniform/per-frame durations, loop, ping-pong; `AnimationPlayer`: named animation registry, play/stop, frame advancement, ping-pong, on_finish callback
- `pygame_engine/animation/__init__.py` — now exports `Tween`, `SpriteAnimation`, `AnimationPlayer`
- `pygame_engine/graphics/sprite_renderer.py` — `draw_sprite`: blit with flip/alpha/rotation/scale; `draw_animation_frame`: convenience wrapper for AnimationPlayer
- `pygame_engine/graphics/__init__.py` — now exports `draw_sprite`, `draw_animation_frame`
- `tests/test_animator.py` — 26 tests covering SpriteAnimation construction, AnimationPlayer frame advancement, loop, ping-pong, on_finish, per-frame durations, add_many

### Fixed — Stack widget
- `pygame_engine/ui/containers/stack.py` — `handle_event` now properly follows base Widget contract: updates `hovered` from MOUSEMOTION before the enabled check, skips routing when disabled; added full docstrings

### Added — Tests for Stack and TextBlock
- `tests/test_stack.py` — 20 tests covering child management, event routing order, disabled/invisible guards, hovered update, update/render delegation
- `tests/test_text_block.py` — 20 tests covering dirty flag invalidation, property setters, text wrapping (empty, short, long, newlines, empty paragraphs), render cache behaviour

### Added — Scene transitions
- `pygame_engine/scene/transitions.py` — `Transition` base class; `FadeTransition` (fade through solid colour, two-phase); `SlideTransition` (left/right/up/down, outgoing slides out while incoming slides in); `CrossfadeTransition` (simultaneous dissolve)
- `pygame_engine/scene/scene_manager.py` — `push_with`, `replace_with`, `pop_with` accepting optional transition; `is_transitioning` property; transition render intercept; existing push/pop/replace/clear_and_push unchanged
- `pygame_engine/scene/__init__.py` — updated docstring listing transition imports
- `tests/test_transitions.py` — 20 tests covering progress, is_done, direction validation, render safety, SceneManager integration

### Added — Game project template
- `template/` — complete, runnable game project skeleton

**Structure:**
- `template/main.py` — fully wired entry point (AppConfig, theme, initial scene)
- `template/game/input_actions.py` — re-exports engine actions + game-specific constants
- `template/game/theme.py` — `build_theme()` with dataclass-replace override pattern
- `template/game/saves.py` — `SaveManager` config, migration pipeline, `build_payload`/`restore_payload` stubs
- `template/game/scenes/main_menu.py` — working main menu (New Game/Continue/Settings/Quit, save-aware Continue button)
- `template/game/scenes/game_scene.py` — gameplay scene skeleton with HUD, pause, save hooks
- `template/game/scenes/pause_scene.py` — semi-transparent pause overlay with resume/settings/main-menu
- `template/game/scenes/settings_scene.py` — settings overlay with volume ProgressBars
- `template/README.md` — copy instructions, workflow guide, engine reference table
- `template/assets/` — empty asset directories with .gitkeep
- `template/saves/` — empty saves directory with .gitkeep

### Added — Dropdown widget
- `pygame_engine/ui/controls/dropdown.py` — `Dropdown`: closed button face + floating list via `overlay_render()`, custom values, placeholder, on_change callback, keyboard navigation (arrows/enter/escape), click-outside-to-close, opens above if near bottom of screen
- `pygame_engine/ui/controls/__init__.py` — now exports `Button`, `Dropdown`, `InputField`, `ProgressBar`
- `pygame_engine/ui/__init__.py` — now exports `Dropdown`; also fixed stale docstring
- `tests/test_dropdown.py` — 26 tests covering construction, selection, on_change, open/close, keyboard nav, hit-testing, render safety

### Added — Nine-slice rendering
- `pygame_engine/graphics/nine_slice.py` — `draw_nine_slice()`: scales a source surface into a dest rect preserving corners; `make_nine_slice_surface()`: pre-renders to a new surface; `NineSlicePanel`: lightweight widget-like object with caching; `_normalise_border()`: int or 4-tuple border normalisation
- `pygame_engine/graphics/__init__.py` — now exports `draw_nine_slice`, `make_nine_slice_surface`, `NineSlicePanel`
- `tests/test_nine_slice.py` — 18 tests covering border normalisation, draw geometry, error cases, SRCALPHA preservation, NineSlicePanel caching behaviour

### Added — Focus traversal
- `pygame_engine/ui/focus.py` — `FocusManager` mixin: Tab/Shift+Tab cycling through focusable children, `focus_first`, `focus_none`, keyboard routing to focused child, wrapping
- `pygame_engine/ui/base/widget.py` — `focusable: bool = False` attribute added to base Widget
- `pygame_engine/ui/controls/button.py` — `focusable = True`; keyboard activation (Enter/Space when focused); focus ring drawn when focused
- `pygame_engine/ui/controls/input_field.py` — `focusable = True`; `_on_focus_gained`/`_on_focus_lost` hooks for FocusManager integration
- `pygame_engine/ui/containers/panel.py` — `manage_focus=False` parameter; `FocusManager` mixin integrated; Tab intercept in `_handle_event_widget`
- `pygame_engine/ui/containers/stack.py` — same as Panel
- `tests/test_focus.py` — 22 tests covering child filtering, Tab/Shift+Tab, wrap-around, focus_first/none, no-focusable edge cases, default focusable values

### Added — Particle system
- `pygame_engine/particles/particle.py` — `Particle`: data container with position, velocity, acceleration, colour, size, alpha, lifetime, drag; `progress` and `is_dead` properties
- `pygame_engine/particles/emitter.py` — `Emitter`: continuous emission (`start`/`stop`) and one-shot bursts, physics (gravity, drag, fade, shrink), `render()` with alpha blending, `render_fast()` without; `max_particles` cap
- `pygame_engine/particles/presets.py` — `explosion`, `sparkle`, `smoke`, `fire_emitter`, `trail`, `hit_effect` factory functions
- `pygame_engine/particles/__init__.py` — exports `Emitter`, `Particle`
- `tests/test_particles.py` — 34 tests covering Particle lifecycle, Emitter burst/continuous/update/physics, helpers, all 6 presets

### Added — Test suite completion
- `tests/test_layout.py` — 34 tests: all 9 anchor points with margin/offset, row/column/grid count/size/spacing/alignment/edge cases
- `tests/test_timers.py` — 28 tests: Timer start/stop/reset/restart, progress/elapsed/remaining, zero-duration, Cooldown fire/carry-over/restart
- `tests/test_rects.py` — 32 tests: rect_from_center/corners, inset/inset_xy, snap_to_grid, clamp_inside, split_horizontal/vertical with offset positions
- `tests/test_mathx.py` — 42 tests: clamp/clamp01, remap/remap_clamped, lerp/lerp_clamped, smoothstep/smootherstep, angle_to_vec/vec_to_angle roundtrip, approach
- `tests/test_colors.py` — 36 tests: lerp_color/alpha, brighten, with_alpha clamping, hex_to_rgb (3 and 6 digit, with/without #), rgb_to_hex, hsv_to_rgb, roundtrip
- `tests/test_input_manager.py` — 36 tests: key press/release/held per-frame semantics, action queries with default and custom bindings, mouse pos/delta/buttons/wheel, transient state clearing

### Added — Particles example
- `examples/example_particles.py` — interactive particle demo: all six presets, left-click explosion+sparkle, right-click hit effect, continuous fire+smoke+trail following mouse, F toggles fast/quality render, live particle count in title
- `main.py` — updated to run example_particles by default

### Added — EventBus and Signals
- `pygame_engine/events/event_bus.py` — `EventBus`: pub/sub bus with `on`, `once`, `off`, `emit`, `clear`, `clear_all`; wildcard patterns via fnmatch; broken handler isolation; `handler_count`, `subscribed_events`; module-level `bus` singleton
- `pygame_engine/events/signals.py` — `Signal`: typed wrapper around a specific EventBus event; `connect`, `connect_once`, `disconnect`, `emit`, `clear`
- `pygame_engine/events/__init__.py` — exports `EventBus`, `bus`
- `pygame_engine/app/application.py` — `bus.clear_all()` called on shutdown to prevent stale handlers
- `docs/event_model.md` — full event model documentation: Observable vs EventBus decision guide, naming conventions, Signal usage, accepted decisions
- `tests/test_event_bus.py` — 37 tests covering subscribe/emit/unsubscribe, once, wildcards, duplicates, broken handler isolation, clear, module singleton

### Polish pass
- `docs/roadmap.md` — EventBus marked complete

### Documentation — Final roadmap update
- `docs/roadmap.md` — complete rewrite reflecting true current state: all phases marked complete, full inventory of what's built, Phase 9 framing for game-driven future work

### Cleanup pass — TODOs, docs, test gaps

**application.py — TODOs resolved**
- Removed stale `# TODO: initialise AssetLoader` (was already done 2 lines above)
- Removed stale `# TODO: initialise debug tools if config.debug` (already wired)
- Removed stale `# TODO: debug overlay update` (overlay renders in step 7, no separate update needed)
- Removed stale `# TODO: shutdown debug tools` (shutdown works; no separate step needed)
- Replaced `# TODO: notify SceneManager / layout system of new surface size` with a proper docstring explaining the resize behaviour and limitation
- Cleaned up `_startup` comment block, removed redundant field comments
- Tightened all property docstrings to single-line form

**Docs — stale references fixed**
- `docs/accepted_decisions.md` — Decision #19 rewrote from "Events Package Removed" to "EventBus and Signals" (the package now exists and is implemented)
- `docs/architecture.md` — `state/` section: removed `state_store.py`, described actual files; `events/` section: described `EventBus` and `Signal`
- `docs/naming_conventions.md` — replaced `state_store.py` example with `scene_stack.py`, `debug_log.py`
- `docs/state_model.md` — complete rewrite: removed all `state_store.py` planning content, accurately reflects current state (`Observable`, `RuntimeFlags` only), updated "Open Questions" section removed (all answered)

**Tests — gaps filled**
- `tests/test_panel.py` — new: 20 tests covering child management, event routing order, invisible/disabled guards, hover update, update/render delegation, set_rect, focus management opt-in
- `tests/test_button.py` — added 6 tests: label getter/setter, focusable default, keyboard activation (Enter/Space when focused), keyboard not activated when unfocused, set_rect propagation to label
- `tests/test_widget.py` — added 9 tests: focusable attribute, is_interactive property, set_rect, contains_point, focused default
- `tests/test_scene_manager.py` — added 5 tests: push_with, replace_with, pop_with, is_transitioning true/false
- `tests/test_scene_stack.py` — added 4 tests: top on empty stack, is_empty, clear returns scenes topmost-first

### Fixed — Audit findings

**Real API bugs fixed**
- `pygame_engine/graphics/__init__.py` — was missing actual imports for `nine_slice` and `sprite_renderer`; `draw_nine_slice`, `NineSlicePanel`, `draw_sprite`, `draw_animation_frame` were in `__all__` but not imported. Now correctly imports and exports all graphics helpers.
- `pygame_engine/scene/__init__.py` — transitions were documented as part of the package API but not exported. Now exports `FadeTransition`, `SlideTransition`, `CrossfadeTransition` directly: `from pygame_engine.scene import FadeTransition`

**CONSOLE_TOGGLE wired**
- `pygame_engine/state/runtime_flags.py` — added `show_console: bool` flag; `enable_debug_all()` now also sets `show_console = True`
- `pygame_engine/debug/console.py` — now checks `flags.show_console` (was incorrectly sharing `flags.show_overlay`)
- `pygame_engine/app/application.py` — `CONSOLE_TOGGLE` (F3) now wired: toggles `flags.show_console`

**Scene overlay render pass**
- `pygame_engine/scene/scene.py` — `render()` now calls `overlay_render(surface)` as a second pass after the widget tree. Subclasses override `overlay_render()` for Dropdowns, Tooltips, and other floating UI. Default is no-op.

**Template fixes**
- `game_template/README.md` — complete rewrite: correct copy command (`xcopy` for Windows, `cp -r` for macOS/Linux), correct bindings guidance, F3 console toggle documented
- `game_template/main.py` — removed dead `_build_bindings()` function that was defined but never used; bindings are now set in `on_enter` as documented

**Decisions documented**
- `docs/accepted_decisions.md` — Decision #23: Scenes Receive Application Directly; Decision #24: Scene overlay_render Pass
