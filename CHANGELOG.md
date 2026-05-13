# Changelog

All notable changes to `pygame_engine` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `tests/test_application.py` — integration tests for `Application` and `AppConfig`:
  config defaults, construction side-effect-free guarantee, service access guards,
  `_compute_dt` clamping, debug flag activation, `stop()`, theme access,
  `_on_resize`, scene `overlay_render` ordering, event bus cleanup on shutdown

---

## [1.0.0] — Engine complete

This release marks the completion of the engine foundation. All planned systems
are implemented, tested, and documented.

### Runtime spine
- `Application`, `AppConfig` — main loop, delta-time, service wiring, debug integration
- `Scene`, `SceneManager`, `SceneStack` — stack-based scene flow with lifecycle hooks
- `SceneManager` extended with `push_with`, `replace_with`, `pop_with` + `is_transitioning`
- `FadeTransition`, `SlideTransition`, `CrossfadeTransition` — opt-in visual transitions
- `Scene.render()` calls `overlay_render()` as second pass for floating UI

### UI widget library
- `Widget` base — `focusable`, focus ring, `is_interactive`, `contains_point`, `set_rect`
- `Panel`, `Stack` — containers with opt-in `FocusManager` (Tab/Shift+Tab traversal)
- `Scrollable` — clipping viewport with mouse-wheel scroll
- `Button` — keyboard-activatable when focused; focus ring
- `Dropdown` — floating list via `overlay_render()` z-ordering pattern
- `InputField` — TEXTINPUT events, cursor, placeholder, password mode
- `ProgressBar` — horizontal/vertical fill bar
- `Label`, `TextBlock` — text display with render caching
- `Toast`, `Tooltip` — feedback widgets
- `FocusManager` mixin — Tab traversal for Panel and Stack

### Layout and theme
- `anchor`, `row`, `column`, `grid` — stateless layout helpers (all 9 anchor points)
- Theme system: tokens → defaults → runtime, fully swappable

### Input
- `InputManager` — press/release/held per-frame semantics, action queries, mouse, wheel
- Actions: `CONFIRM`, `CANCEL`, `PAUSE`, `NAV_*`, `DEBUG_TOGGLE`, `INSPECTOR_TOGGLE`, `CONSOLE_TOGGLE`
- Default bindings: F1=debug overlay, F2=inspector, F3=console

### Animation
- `Tween` — single-value animator, 30 easing functions (all Robert Penner families)
- `SpriteAnimation` — immutable frame data, uniform/per-frame durations, loop, ping-pong
- `AnimationPlayer` — named animation registry, on_finish callback

### Graphics
- `draw_utils` — themed rect drawing, chevrons, lines
- `surfaces` — alpha surface helpers
- `sprite_renderer` — `draw_sprite`, `draw_animation_frame` with flip/alpha/rotation/scale
- `nine_slice` — `draw_nine_slice`, `NineSlicePanel` with caching

### Assets and audio
- `AssetLoader` — lazy-cached images, spritesheets, fonts, sounds; debug placeholders
- `AudioManager` — music streaming, SFX channels, master/music/sfx volume, mute

### Persistence
- `storage` — atomic writes, `.bak` backups, corrupt save detection
- `serializers` — dataclass to/from dict, safe coercion helpers
- `migrations` — version upgrade pipeline with decorator-based handler registration
- `SaveManager` — slot management, game_id validation, automatic migration on load

### State and events
- `Observable[T]` — reactive value wrapper with subscribe/unsubscribe
- `RuntimeFlags` — `debug`, `show_fps`, `show_rects`, `show_overlay`, `show_console`; module-level singleton
- `EventBus` — pub/sub, wildcard patterns, one-shot, broken handler isolation; module-level `bus`
- `Signal` — typed wrapper around a specific EventBus event

### Particles
- `Emitter` — continuous + burst emission, gravity, drag, alpha/fast render
- `Particle` — lightweight data container
- Presets: `explosion`, `sparkle`, `smoke`, `fire_emitter`, `trail`, `hit_effect`

### Debug
- `debug_log` — centralised log with level/tag filtering, capped history
- `DebugOverlay` — FPS, scene info, active flags; self-checks `flags.show_overlay` (F1)
- `DebugConsole` — on-screen log tail; self-checks `flags.show_console` (F3)
- `Inspector` — scene/widget tree dump to debug log (F2)

### Utils
- `Timer`, `Cooldown` — delta-time driven timers
- `mathx` — clamp, lerp, remap, smoothstep, angle_to_vec, approach
- `colors` — lerp_color, brighten, hex_to_rgb, hsv_to_rgb
- `rects` — inset, snap_to_grid, clamp_inside, split helpers

### Game template
- `game_template/` — immediately runnable skeleton: wired main.py, working main
  menu, pause scene, settings scene (Dropdown + ProgressBar volume + overlay_render),
  game scene stub, documented model/system/ui packages, Windows + macOS/Linux README

### Test suite
- 669+ tests across 28 files covering every deterministic system in the engine

### Documentation
- 20 docs covering every system with locked architecture decisions
- `accepted_decisions.md` — 24 decisions recorded including scene app-coupling (#23)
  and overlay_render pass (#24)
- `roadmap.md` — all 8 phases marked complete; Phase 9 framing for game-driven work

### API fixes (audit-driven)
- `graphics/__init__.py` — fixed missing imports for nine_slice and sprite_renderer
- `scene/__init__.py` — transitions now exported at package level
- `CONSOLE_TOGGLE` (F3) wired in Application; `show_console` flag separated from `show_overlay`
- `game_template/game/actions.py` — exports all three debug actions including `CONSOLE_TOGGLE`
