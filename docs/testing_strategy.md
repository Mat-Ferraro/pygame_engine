# Testing Strategy

## Purpose

Testing should support confidence in reusable engine behavior without turning
the project into a test-only exercise.

The goal is to test:
- reusable logic
- contracts with clear expected behavior
- math-heavy or stateful helpers
- input/layout/timing behavior that is easy to regress

---

## Test Location

All automated tests live in `tests/` at the **repo root** (not inside the
`pygame_engine/` package).

```
pygame_engine/          ← repo root
└── tests/
    ├── conftest.py     ← shared fixtures (headless pygame init)
    ├── test_easing.py
    ├── test_layout.py
    ├── test_rects.py
    └── test_timers.py
```

`pyproject.toml` configures pytest to look in `tests/`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## Headless Pygame Setup

`tests/conftest.py` provides a session-scoped `pygame_init` fixture that
initialises pygame without opening a display window. It runs automatically
for the entire test session.

This allows tests to use `pygame.Rect`, `pygame.Surface`, and similar
primitives in CI environments with no display available.

A `display_surface` fixture returns a small `pygame.Surface(800, 600)` for
tests that need a surface to draw onto.

---

## Current Test Suite

Starter tests already exist for:
- `test_easing.py` — easing function correctness
- `test_layout.py` — layout rect calculations
- `test_rects.py` — rect math helpers
- `test_timers.py` — timer behavior

These are good early targets because they are deterministic and reusable.

---

## What Should Be Tested

High-value unit test targets:
- easing functions and tween progression
- timer behavior (tick, elapsed, done)
- rect math helpers
- layout calculations (row, column, grid, anchor)
- input transition logic (pressed, released, held)
- state helpers
- event bus subscription and dispatch behavior
- theme resolution logic
- scene stack mechanics (push, pop, blocking policy)

---

## What Usually Does Not Need Heavy Unit Testing Early

Lower-value early targets:
- simple pass-through wrappers
- trivial data containers
- purely visual rendering appearance
- example/demo scripts

These may still deserve smoke tests or manual verification, but not necessarily
deep unit test effort early on.

---

## Types of Tests

### Unit tests
Fast, isolated, deterministic tests for reusable behavior.

### Smoke tests
Simple tests that prove a core object can initialise without crashing.

### Manual example validation
Use `examples/` for visual and behavioral verification that is awkward to
fully automate.

---

## File Naming

`test_<module>.py` — one file per logical area.

Possible future split if the suite grows large:
```
tests/
  unit/
  integration/
  smoke/
```

Not required yet. Keep it flat until there is a real reason to split.

---

## Good Testing Principles

1. Prefer deterministic tests.
2. Test behavior, not implementation details.
3. Keep tests small and focused.
4. Use examples for visual/manual checks.
5. Add tests when a bug is fixed so it stays fixed.

---

## Test Priorities by Phase

### Early phase (current)
- math helpers
- timers
- layout
- easing/tween logic

### Mid phase
- scene stack behavior
- input manager transition logic
- event bus behavior
- theme/style resolution

### Later phase
- widget interaction behavior
- higher-level runtime smoke tests
- app bootstrap tests

---

## Rendering Tests

Rendering is harder to unit test directly.

Recommended approach:
- test the math and state that drive rendering
- use manual visual examples for appearance checks
- consider screenshot/golden tests only if later justified

---

## Regression Testing

Whenever a bug is fixed:
- add a small test if the bug came from deterministic logic
- update docs/contracts if the bug exposed unclear expected behavior

---

## Rules for Future Development

1. Test reusable logic first.
2. Avoid overtesting trivial code.
3. Prefer behavior-level assertions.
4. Use examples to supplement tests for visual systems.
5. Let real bugs drive valuable regression tests.

---

## Open Questions

- Should there be a dedicated smoke-test suite for core runtime creation?
- Should widget interaction tests use the `display_surface` fixture?
- Should CI run tests once the repo stabilises?
