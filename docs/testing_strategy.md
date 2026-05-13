# Testing Strategy

## Purpose

Testing supports confidence in reusable engine behavior without turning the
project into a test-only exercise.

The goal is to test:
- reusable logic with clear expected behavior
- math-heavy or stateful helpers
- input/layout/timing behavior that is easy to regress
- contracts between systems

---

## Test Location

All automated tests live in `tests/` at the **repo root**.

```
pygame_engine/
└── tests/
    ├── conftest.py          ← shared fixtures
    ├── test_application.py
    ├── test_animator.py
    ├── test_button.py
    ├── test_colors.py
    ├── test_debug_log.py
    ├── test_dropdown.py
    ├── test_easing.py
    ├── test_event_bus.py
    ├── test_focus.py
    ├── test_input_field.py
    ├── test_input_manager.py
    ├── test_layout.py
    ├── test_mathx.py
    ├── test_nine_slice.py
    ├── test_panel.py
    ├── test_particles.py
    ├── test_persistence.py
    ├── test_progress_bar.py
    ├── test_rects.py
    ├── test_scene_manager.py
    ├── test_scene_stack.py
    ├── test_scrollable.py
    ├── test_stack.py
    ├── test_state.py
    ├── test_text_block.py
    ├── test_timers.py
    ├── test_transitions.py
    ├── test_tween.py
    └── test_widget.py
```

`pyproject.toml` configures pytest to look in `tests/`.

---

## Headless Pygame Setup

`tests/conftest.py` provides a session-scoped `pygame_init` fixture that
initialises pygame without opening a display window. It runs automatically
for the entire test session.

A `display_surface` fixture returns a `pygame.Surface(800, 600)` for
tests that need a surface to draw onto.

---

## Current Test Suite

700+ tests across 29 files covering:

| File | Covers |
|---|---|
| `test_application.py` | `AppConfig` defaults, side-effect-free construction, service guards, `_compute_dt` clamping, debug flags, `stop()`, resize, overlay render ordering, bus cleanup |
| `test_animator.py` | `SpriteAnimation`, `AnimationPlayer` frame advancement, ping-pong, on_finish |
| `test_button.py` | Click semantics, keyboard activation, focus, label, set_rect |
| `test_colors.py` | `lerp_color`, `brighten`, `hex_to_rgb`, `hsv_to_rgb`, roundtrip |
| `test_debug_log.py` | Level/tag filtering, timestamps, clear |
| `test_dropdown.py` | Selection, on_change, keyboard nav, hit-testing, overlay render |
| `test_easing.py` | All 30 easing functions: boundary values, monotonicity, overshoot |
| `test_event_bus.py` | Subscribe, emit, unsubscribe, once, wildcards, broken-handler isolation |
| `test_focus.py` | Tab/Shift+Tab traversal, focusable filtering, wrap-around |
| `test_input_field.py` | Insertion, cursor movement, backspace, callbacks, password mode |
| `test_input_manager.py` | Press/release/held per-frame semantics, actions, mouse, wheel |
| `test_layout.py` | All 9 anchor points, row/column/grid with spacing/alignment |
| `test_mathx.py` | clamp, lerp, remap, smoothstep, angle_to_vec, approach |
| `test_nine_slice.py` | Border normalisation, scaling, SRCALPHA, NineSlicePanel caching |
| `test_panel.py` | Child management, event routing, focus management, update/render |
| `test_particles.py` | Particle lifecycle, emitter burst/continuous/physics, all 6 presets |
| `test_persistence.py` | Storage, serializers, migrations, SaveManager slot management |
| `test_progress_bar.py` | Value clamping, fill rect math, directions |
| `test_rects.py` | inset, snap_to_grid, clamp_inside, split helpers |
| `test_scene_manager.py` | Lifecycle hooks, push_with/replace_with/pop_with, is_transitioning |
| `test_scene_stack.py` | Event routing, update/render blocking policy, clear |
| `test_scrollable.py` | Scroll clamping, child offset routing, wheel events |
| `test_stack.py` | Child management, event routing order, hover update |
| `test_state.py` | Observable subscribe/notify/unsubscribe, RuntimeFlags toggle/reset |
| `test_text_block.py` | Dirty flag, text wrapping, cache rebuild |
| `test_timers.py` | Timer progress/elapsed/remaining, Cooldown carry-over |
| `test_transitions.py` | Progress, is_done, direction validation, SceneManager integration |
| `test_tween.py` | Value progression, loop, ping-pong, easing |
| `test_widget.py` | Visibility/enabled guards, focusable, is_interactive, hovered |

---

## What Should Be Tested

High-value unit test targets:
- Deterministic math (easing, layout, rects, mathx, colors)
- State machine behavior (input transitions, timer states, observable callbacks)
- Contract behavior (event routing, focus traversal, widget lifecycle)
- Edge cases (empty stacks, zero-duration timers, clamped values)

---

## What Usually Does Not Need Unit Testing

Lower-value targets:
- Simple pass-through wrappers
- Purely visual rendering appearance
- Example/demo scripts

These are covered by manual validation via `examples/` and the game template.

---

## Types of Tests

### Unit tests
Fast, isolated, deterministic tests for reusable behavior. The vast majority
of the suite.

### Smoke tests
Prove a core object can initialise and render without crashing.
Most widget tests include a `render_does_not_raise` test.

### Manual example validation
Use `examples/` for visual and behavioral verification that is awkward to
automate. Run `python main.py` to verify the particles example.

---

## File Naming

`test_<module>.py` — one file per logical area. The suite is flat — no
subdirectories needed at current scale.

---

## Good Testing Principles

1. Prefer deterministic tests.
2. Test behavior, not implementation details.
3. Keep tests small and focused.
4. Use examples for visual/manual checks.
5. Add tests when a bug is fixed so it stays fixed.
6. No feature is complete until code, tests, examples, and docs all agree.

---

## Rendering Tests

Rendering is harder to unit test directly.

Recommended approach:
- Test the math and state that drive rendering
- Add `render_does_not_raise(display_surface)` smoke tests for every widget
- Use manual visual examples for appearance checks

---

## Regression Testing

Whenever a bug is fixed:
- Add a small test if the bug came from deterministic logic
- Update docs/contracts if the bug exposed unclear expected behavior
