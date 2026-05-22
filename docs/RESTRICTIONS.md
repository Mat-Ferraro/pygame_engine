# pygame_engine — Restriction Reference

**Version:** 1.3.0 design phase
**Authority:** `ARCHITECTURE.md` Section 7

This document is the quick-reference form of the restriction set.
For the full rationale of each restriction, see `ARCHITECTURE.md`.

The restrictions exist because **scalability, maintainability, and
editability are not features you add later — they are properties of
decisions made now.** The cost of making these decisions correctly is low.
The cost of undoing them is high.

---

## How to Use This Document

Before adding any new code, check the restriction that applies:

- Adding a new public API → R5, R15, R16
- Adding a new class with inheritance → R8, R6
- Adding state to a module → R9
- Adding a cross-scene dependency → R7, R4
- Adding a thread → R13
- Adding a feature without tests → R11
- Adding anything that imports from `editor/` in engine code → R14

---

## The Restrictions

### R1 — Behaviour Must Be Statically Traceable
No eval(), exec(), or runtime code generation in production code paths.
Behaviour must be determinable by reading the code without executing it.
Scope: production code. Debug tools and editor may use dynamic features
within editor/ and testing/.
Enforcement: Code review. Static analysis tools must understand the code.

---

### R2 — No Circular Dependencies
The module import graph must be a DAG. No circular imports.
Enforcement: CI script — imports every module in isolation, fails build
on circular imports. Runs on every commit. Zero exceptions.

---

### R3 — Engine Has No Opinions About Game Data
Every engine component must pass the modularity test: "Can a developer
building a completely different game use this without modification?"
If no, it belongs in the game layer.
Banned: Any game-specific concept in pygame_engine/.
Enforcement: Code review.

---

### R4 — Dependency Direction Is Explicit
Lower layers never import from higher layers.
  Layer 0: Observable, EventBus, TimeManager, AssetManager, SaveManager
  Layer 1: Widget, Scene, InputManager, AudioManager, FocusManager
  Layer 2: SceneManager, Panel, Stack, DescribedScene, GizmoRenderer
  Layer 3: Editor, MusicPlayer, InputRecorder, SceneTestHarness
Enforcement: CI script validates import paths against stated hierarchy.

---

### R5 — Public API Grows Deliberately and Consistently
Each public API addition must: (1) pass the modularity test, (2) serve
at least two hypothetical games, (3) be the single idiomatic way to
achieve its purpose. No addition creates a second way to do something
already in the public API.
Enforcement: Code review at PR stage.

---

### R6 — Configuration Uses Data, Not Subclassing
Engine extension points accept data (parameters, dataclasses, class
references), not subclasses to override.
Exception: Scene and Widget are designed for subclassing.
Enforcement: Code review.

---

### R7 — Scenes Do Not Import Each Other
No scene imports another scene at module level. Navigation uses
SceneManager or the scene registry.
Target state: Registry-based navigation via @register_scene.
Enforcement: CI check for cross-scene module-level imports.

---

### R8 — Maximum Inheritance Depth of Three
No class is more than three levels deep. Compose instead of extending.
Mixins: Permitted at depth two only.
Enforcement: Code review.

---

### R9 — No Stateful Singletons
All engine state lives on the Application instance. Module-level state
is for constants and pure functions only.
Current violation to fix: get_theme() singleton must move to Application.
Enforcement: Code review. Tests catching state leaking between instances.

---

### R10 — Widget Render Methods Must Be Pure Given State
render(surface) must produce identical output for the same widget state.
No clock reading, no randomness, no side effects beyond drawing.
Animation via state changes in update(dt), not time-dependent rendering.
Enforcement: Code review.

---

### R11 — No Feature Without a Test (Tiered)
Engine core: Full coverage. Property-based tests for complex logic.
Engine modules: Integration tests + unit tests.
Game scenes: Smoke tests only.
Editor/debug tools: Best effort.
Enforcement: CI must pass. No merge without passing tests.

---

### R12 — No Silent Failures
Every operation either succeeds with stated postconditions, or fails
visibly via exception or event. Nothing leaves an undefined intermediate
state. Postconditions documented in docstrings and tested.
Enforcement: Code review. Tests for failure modes.

---

### R13 — No Game Logic Threading
Game logic on main thread only.
Permitted background threads: asset loading (preload), audio streaming,
debug server (read-only), input recorder (append-only).
Coroutines (async/await) permitted on main thread.
Enforcement: Code review.

---

### R14 — Editor Is Always Optional, Enforced by CI
CI job 1: Run all tests with editor/ deleted. Failures = violation.
CI job 2: Import every engine module, assert no import from editor/.
Enforcement: Automated CI. Cannot be overridden by convention.

---

### R15 — Every Public API Has a Docstring
Every public method in the stable API tier documents: what it does,
parameters, return value, exceptions, postconditions.
Enforcement: ruff/pydocstyle in CI. Fails for pygame_engine/ public modules.

---

### R16 — Naming Conventions Are Enforced
Classes: PascalCase, no abbreviations.
Methods/properties: snake_case. Verbs for actions, nouns for properties.
Booleans: is_, has_, can_, should_ prefixes.
Events: dot-separated noun-first. engine.scene.changed not on_scene_changed.
Files: snake_case.py. One primary class per file.
Constants: UPPER_SNAKE_CASE. No inline magic numbers.
No abbreviations in public identifiers:
  Banned: sw, sh, btn, cb, fn, idx, col (when ambiguous)
  Permitted standard terms: dt, fps, ui, x/y/w/h
Enforcement: ruff with project config. Fails CI for pygame_engine/.

---

### R17 — File Length Limits
Soft limit: 400 lines. Review for decomposition.
Hard cap: 600 lines. No new features until decomposed.
Current violations requiring action:
  management_scene.py ~937L — hard cap exceeded
  game_hub_scene.py ~619L — hard cap exceeded
  inventory_scene.py ~600L — at hard cap
Enforcement: CI warning at soft limit. Code review enforces hard cap.

---

### R18 — Engine Scope Is 2D Interactive Applications
Features within the scope of interactive 2D applications are welcome.
Features outside (physics simulation, 3D rendering, networking) are not
the engine's responsibility. Integrate external libraries for those needs.
Physics boundary: rect collision utilities provided, simulation is not.
Recommended physics library: pymunk.

---

### R19 — pygame-ce Version Is Pinned
Specific version pinned in pyproject.toml. Not a range.
Upgrade: update pin, run full tests, check changelog, fix breaks,
note in CHANGELOG, release.
Document tested version in README and __init__.py.

---

### R20 — Layout Descriptor Is the Only Editor/Scene Interface
The editor reads and writes scene state only through SceneDescriptor
and its observable properties. No direct access to scene instance vars.
Enforcement: Code review. Architectural boundary in DescribedScene design.

---

### R-C — Stateful Widgets Implement a State Interface
Widgets with meaningful runtime state implement:
  capture_state(self) -> dict
  restore_state(self, state: dict) -> None
The editor calls these around hot reloads to preserve state.

---

## Restriction Quick Matrix

Adding a new public class or method:        R5, R15, R16
Adding inheritance to an existing class:    R8
Adding module-level mutable state:          R9
Adding a cross-scene import:                R7, R4
Adding a background thread:                 R13
Adding a feature without tests:             R11
Importing from editor/ in engine code:      R14
Adding a game concept in engine code:       R3
Adding a configuration pattern:             R6
Calling eval() or exec():                   R1
A file growing past 400 lines:              R17
A method with no docstring:                 R15
An abbreviation in a public name:           R16

---

## What the Restrictions Cost

We give up:
  Convenience — auto-generation, public-by-default, flexible threading
  Flexibility — one way to do things, version pinning, explicit promotion
  Scope — no physics, no genre-specific modules, no game concepts in engine

We get in return:
  Every feature is testable in isolation
  The engine works correctly with any 2D game without modification
  Breaking changes are explicit and versioned
  The editor can be removed without touching game code
  Performance characteristics are predictable
  The codebase stays readable because there is one way to do each thing
