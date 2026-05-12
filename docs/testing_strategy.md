# Testing Strategy

## Purpose

Testing should support confidence in reusable engine behavior without turning the project into a test-only exercise.

The goal is to test:
- reusable logic
- contracts with clear expected behavior
- math-heavy or stateful helpers
- input/layout/timing behavior that is easy to regress

---

## Current Test Direction

The project already includes starter tests for:
- easing
- layout
- rect helpers
- timers

These are good early targets because they are deterministic and reusable.

---

## What Should Be Tested

High-value unit test targets:
- easing functions
- tween progression
- timer behavior
- rect math
- layout calculations
- input transition logic
- state helpers
- event bus subscription/dispatch behavior
- theme resolution logic
- scene stack mechanics where reasonably testable

---

## What Usually Does Not Need Heavy Unit Testing Early

Lower-value early targets:
- simple pass-through wrappers
- trivial data containers
- purely visual rendering appearance
- example/demo scripts

These may still deserve smoke tests or manual verification, but not necessarily deep unit test effort early on.

---

## Types of Tests

### Unit tests
Fast, isolated, deterministic tests for reusable behavior.

### Smoke tests
Simple tests that prove an example or core object can initialize without crashing.

### Manual example validation
Use the `examples/` folder for visual and behavioral verification that is awkward to fully automate.

---

## Test Organization

Recommended file naming:
- `test_<module>.py`

Recommended rule:
- keep tests near conceptual areas, not giant mixed test files

Possible future split:
- `tests/unit/`
- `tests/integration/`
- `tests/smoke/`

Not required yet.

---

## Good Testing Principles

1. Prefer deterministic tests.
2. Test behavior, not implementation details.
3. Keep tests small and focused.
4. Use examples for visual/manual checks.
5. Add tests when a bug is fixed so it stays fixed.

---

## Test Priorities by Phase

### Early phase
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

This helps the engine mature over time.

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
- Should widget interaction tests use headless pygame setup?
- Should CI run tests later once the repo stabilizes?
