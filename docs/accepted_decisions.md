# Accepted Decisions

## Purpose

This document records the currently accepted architecture decisions for
`pygame_engine`.

These are the decisions the engine should follow unless they are later revised
through the normal documentation and decision-log process.

---

## Accepted Decisions

### 1. Engine Scope
`pygame_engine` is a **lightweight reusable framework** over pygame.

It should provide:
- application/runtime structure
- scene flow
- UI primitives
- layout helpers
- theme support
- input abstraction
- shared asset/audio/debug helpers

It should **not** try to be a full genre-specific gameplay engine in version one.

---

### 2. Repository Layout
The repo has four top-level areas:

| Path              | Role                                       |
|-------------------|--------------------------------------------|
| `pygame_engine/`  | The importable Python package              |
| `docs/`           | Architecture and system documentation      |
| `examples/`       | Runnable examples and manual smoke tests   |
| `tests/`          | Automated test suite                       |

`docs/`, `examples/`, and `tests/` live at the **repo root**, not inside the
importable package. This keeps the installed package clean.

---

### 3. Public API Style
Preferred consumer imports are clean, top-level:

```python
from pygame_engine.ui import Button
from pygame_engine.scene import Scene
```

Deep imports remain possible internally, but the engine should expose a stable
and clean public import surface.

---

### 4. Scene Model
The runtime should be **stack-based**.

`SceneManager` should own or coordinate a `SceneStack`.

Scene replacement is treated as a convenience operation on top of the stack
model rather than as a totally separate mental model.

---

### 5. Event Consumption
Scene and widget event handlers should return a boolean:

- `True` = event consumed
- `False` = event not consumed

```python
handle_event(event) -> bool
```

This supports overlays, modal UI, focused widgets, and layered input routing.

---

### 6. Input Routing Priority
Recommended routing order:

1. Application-level essential handling
2. Topmost/modal scene or overlay
3. Focused widget / UI layer
4. Scene-level logic
5. Global debug/runtime shortcuts

---

### 7. Scene and UI Relationship
Scenes may optionally own a `root_widget`.

- scene = flow, coordination, high-level runtime behavior
- root widget tree = detailed UI composition and interaction

---

### 8. Widget Hierarchy Policy
The base `Widget` should **not** automatically own child-management behavior.

Child-management belongs to container widgets.

---

### 9. Layout Scope for V1
Version one layout should use:
- assigned rects
- simple layout helpers
- predictable row/column/grid/anchor behavior

Version one should **not** implement a full advanced measurement/layout engine.
Layout should be designed so it can be expanded later.

---

### 10. Theme Access
Widgets may access styling through a stable runtime theme interface.

- engine-defined defaults
- runtime theme access
- support for future local overrides

Widgets should not hardcode visual values everywhere.

---

### 11. Asset Loading
Default asset loading philosophy:
- lazy load with caching
- fail loudly during engine/framework development

Placeholder fallback behavior may be added later.

---

### 12. Debug Tools
Debug tools are important and well supported, but they remain **optional runtime
layers**, not hard dependencies of the core application loop.

---

### 13. State Philosophy
Shared engine state should remain limited to **engine-level runtime state**.

The engine should not become the home for game-specific domain state.

---

### 14. Typing Philosophy
Use **moderate but intentional typing**.

Type: public contracts, important runtime interfaces, reusable helpers.
Avoid blocking early development with extreme strictness.

---

### 15. Version One Boundary
The accepted version one target includes:
- `Application`, `Scene`, `SceneManager`, `SceneStack`
- `Widget`, `Panel`, `Button`, `Label`, `TextBlock`
- Basic row/column layout
- Theme runtime/defaults
- Input manager/actions/bindings
- Basic asset loading
- Examples

Other systems may follow later.

---

### 16. Testing Infrastructure
- Tests live in `tests/` at the repo root.
- `tests/conftest.py` provides a headless pygame session fixture.
- `pyproject.toml` configures `testpaths = ["tests"]`.

---

### 17. Documentation Discipline
Documentation should be updated whenever:
- a core contract changes
- a framework-wide design decision is made
- a naming/organisation rule changes

Use:
- deeper docs for system detail
- `decision_log.md` for concise historical decisions
- `CHANGELOG.md` for notable structural or behavioral changes

---

## Future Revisions

These decisions are intentionally stable, but not permanent.

If future engine use proves that a better direction exists, revise:
1. the decision log
2. the affected system docs
3. this accepted-decisions document
