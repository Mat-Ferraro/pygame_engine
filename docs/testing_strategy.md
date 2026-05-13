---

## Test Location

All automated tests live in `tests/` at the repo root.

```
tests/
├── conftest.py
├── test_animation_state_machine.py
├── test_animator.py
├── test_application.py
├── test_atlas.py
├── test_button.py
├── test_camera.py
├── test_checkbox.py
├── test_colors.py
├── test_debug_log.py
├── test_dialogue.py
├── test_dropdown.py
├── test_easing.py
├── test_event_bus.py
├── test_focus.py
├── test_input_field.py
├── test_input_manager.py
├── test_layout.py
├── test_lighting.py
├── test_locale.py
├── test_mathx.py
├── test_nine_slice.py
├── test_panel.py
├── test_particles.py
├── test_pathfinding.py
├── test_persistence.py
├── test_positional_audio.py
├── test_progress_bar.py
├── test_radio_group.py
├── test_rects.py
├── test_responsive_layout.py
├── test_scene_manager.py
├── test_scene_stack.py
├── test_screen_manager.py
├── test_scrollable.py
├── test_slider.py
├── test_stack.py
├── test_state.py
├── test_text_block.py
├── test_tilemap.py
├── test_timers.py
├── test_transitions.py
├── test_tween.py
└── test_widget.py
```

---

## Headless Setup

`conftest.py` provides a session-scoped `pygame_init` fixture that
initialises pygame without a display window. A `display_surface` fixture
returns an 800×600 surface for render smoke tests.

---

## Current Suite — 1083+ tests across 42 files

| File | Covers |
|---|---|
| `test_animation_state_machine.py` | States, transitions, priority, any-state, on_enter/on_exit, bad-condition safety |
| `test_animator.py` | `SpriteAnimation`, `AnimationPlayer` — frame advancement, ping-pong, on_finish |
| `test_application.py` | `AppConfig`, construction, service guards, dt clamping, debug flags, resize, bus cleanup |
| `test_atlas.py` | `AtlasPacker` packing, `SpriteAtlas` blit/get_rect/save/load |
| `test_button.py` | Click semantics, keyboard activation, focus, label, set_rect |
| `test_camera.py` | Coordinate conversion, follow, zoom, shake, bounds, culling |
| `test_checkbox.py` | Toggle, on_change, click, keyboard activation |
| `test_colors.py` | `lerp_color`, `brighten`, `hex_to_rgb`, `hsv_to_rgb`, roundtrip |
| `test_debug_log.py` | Level/tag filtering, timestamps, clear |
| `test_dialogue.py` | Script validation, runner state machine, box typewriter/choices |
| `test_dropdown.py` | Selection, on_change, keyboard nav, hit-testing, overlay render |
| `test_easing.py` | All 30 easing functions: boundary values, monotonicity, overshoot |
| `test_event_bus.py` | Subscribe, emit, unsubscribe, once, wildcards, broken-handler isolation |
| `test_focus.py` | Tab/Shift+Tab traversal, focusable filtering, wrap-around |
| `test_input_field.py` | Insertion, cursor movement, backspace, callbacks, password mode |
| `test_input_manager.py` | Press/release/held per-frame semantics, actions, mouse, wheel |
| `test_layout.py` | All 9 anchor points, row/column/grid with spacing/alignment |
| `test_lighting.py` | `Light` defaults/clamp, `LightingSystem` add/remove/render/camera |
| `test_locale.py` | Load, lookup, fallback, plural forms, format substitution, hot-swap |
| `test_mathx.py` | clamp, lerp, remap, smoothstep, angle_to_vec, approach |
| `test_nine_slice.py` | Border normalisation, scaling, SRCALPHA, NineSlicePanel caching |
| `test_panel.py` | Child management, event routing, focus management, open-Dropdown priority |
| `test_particles.py` | Particle lifecycle, emitter burst/continuous/physics, all 6 presets |
| `test_pathfinding.py` | `ObstacleGrid` set/fill/bounds, `Pathfinder` A*/diagonal/corner-cutting |
| `test_persistence.py` | Storage, serializers, migrations, SaveManager slot management |
| `test_positional_audio.py` | Listener, distance falloff, stereo panning, base volume scaling |
| `test_progress_bar.py` | Value clamping, fill rect math, directions |
| `test_rich_label.py` | `RichLabel` widget, `parse_markup()`, hex parser, font cache |
| `test_radio_group.py` | Selection, on_change, keyboard navigation |
| `test_rects.py` | inset, snap_to_grid, clamp_inside, split helpers |
| `test_responsive_layout.py` | FlexRow/FlexColumn weights/fixed/spacing, AnchorLayout rules |
| `test_scene_manager.py` | Lifecycle hooks, push_with/replace_with/pop_with, is_transitioning |
| `test_scene_stack.py` | Event routing, update/render blocking, clear |
| `test_screen_manager.py` | on_resize hook, notify_resize, bus event, screen_rect |
| `test_scrollable.py` | Scroll clamping, child offset routing, wheel events |
| `test_slider.py` | Value clamping, keyboard, click, normalised, on_change |
| `test_stack.py` | Child management, event routing order, hover update |
| `test_state.py` | Observable subscribe/notify/unsubscribe, RuntimeFlags toggle/reset |
| `test_text_block.py` | Dirty flag, text wrapping, cache rebuild |
| `test_theme_loader.py` | `theme_from_file()`, partial override, roundtrip, `reload_theme_file()`, `theme_to_dict()` |
| `test_tilemap.py` | Tileset slicing, TileLayer grid, Tilemap collision/rendering |
| `test_timers.py` | Timer progress/elapsed/remaining, Cooldown carry-over |
| `test_transitions.py` | Progress, is_done, direction validation, SceneManager integration |
| `test_tween.py` | Value progression, loop, ping-pong, easing |
| `test_widget.py` | Visibility/enabled guards, focusable, is_interactive, hovered |

---

## What to Test

High-value: deterministic math, state machine behaviour, contract behaviour, edge cases.

Low-value: simple pass-through wrappers, purely visual appearance, demo scripts.

## Test Types

- **Unit** — fast, isolated, deterministic. The vast majority.
- **Smoke** — `render_does_not_raise(display_surface)` on every widget.
- **Manual** — use `examples/` for visual and behavioural verification.

## Principles

1. Test behaviour, not implementation details.
2. Add a test when a bug is fixed so it stays fixed.
3. No feature is complete until code, tests, examples, and docs all agree.
========================================================================================================================