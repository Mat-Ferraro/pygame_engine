# Accepted Decisions

## Purpose

This document records the currently accepted architecture decisions for `pygame_engine`.

These are the decisions the engine should follow unless they are later revised through the normal documentation and decision-log process.

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

This may expand later if real use shows that expansion is valuable.

---

### 2. Public API Style
Preferred consumer imports are clean, top-level imports such as:

```python
from pygame_engine.ui import Button
from pygame_engine.scene import Scene
```

Deep imports should remain possible internally, but the engine should expose a stable and clean public import surface.

---

### 3. Scene Model
The runtime should be **stack-based**.

`SceneManager` should own or coordinate a `SceneStack`.

Scene replacement is treated as a convenience operation on top of the stack model rather than as a totally separate mental model.

---

### 4. Event Consumption
Scene and widget event handlers should return a boolean:

- `True` = event consumed
- `False` = event not consumed

Recommended contract:

```python
handle_event(event) -> bool
```

This supports overlays, modal UI, focused widgets, and layered input routing.

---

### 5. Input Routing Priority
Recommended routing philosophy:

1. application-level essential handling
2. topmost/modal scene or overlay
3. focused widget / UI layer
4. scene-level logic
5. global debug/runtime shortcuts

Exact implementation details may evolve, but this ordering philosophy is accepted.

---

### 6. Scene and UI Relationship
Scenes may optionally own a `root_widget`.

Recommended split:
- scene = flow, coordination, high-level runtime behavior
- root widget tree = detailed UI composition and interaction

This should help prevent scene classes from becoming bloated with low-level UI details.

---

### 7. Widget Hierarchy Policy
The base `Widget` should **not** automatically own child-management behavior.

Child-management behavior belongs to container widgets.

This keeps the base widget smaller, clearer, and easier to reason about.

---

### 8. Layout Scope for V1
Version one layout should use:
- assigned rects
- simple layout helpers
- predictable row/column/grid/anchor behavior

Version one should **not** attempt to implement a full advanced measurement/layout engine.

However, layout should be designed so it can be expanded later if the engine grows into that need.

---

### 9. Theme Access
Widgets may access styling through a stable runtime theme interface.

Recommended direction:
- engine-defined defaults
- runtime theme access
- support for future local overrides

Widgets should not hardcode visual values everywhere.

---

### 10. Asset Loading
Default asset loading philosophy:
- lazy load with caching
- fail loudly during engine/framework development

Placeholder fallback behavior may be added later if useful, but version one should favor clarity and fast failure.

---

### 11. Debug Tools
Debug tools are important and should be well supported, but they should remain **optional runtime layers**, not a hard dependency of the core application loop.

They should integrate cleanly with the engine without distorting core runtime contracts.

---

### 12. State Philosophy
Shared engine state should remain limited to **engine-level runtime state**.

The engine should not become the home for game-specific domain state.

Game-specific state belongs in projects built with the engine.

---

### 13. Typing Philosophy
Use **moderate but intentional typing**.

Type:
- public contracts
- important runtime interfaces
- reusable helpers

Avoid blocking early development with extreme strictness, but do not ignore typing entirely.

---

### 14. Version One Boundary
The accepted version one target includes:
- `Application`
- `Scene`
- `SceneManager`
- `SceneStack`
- `Widget`
- `Panel`
- `Button`
- `Label`
- `TextBlock`
- basic row/column layout
- theme runtime/defaults
- input manager/actions/bindings
- basic asset loading
- examples

Other systems may follow later.

---

### 15. Documentation Discipline
Documentation should be updated whenever:
- a core contract changes
- a framework-wide design decision is made
- a naming/organization rule changes

Use:
- deeper docs for system detail
- `decision_log.md` for concise historical decisions

---

## Future Revisions

These decisions are intentionally stable, but not permanent.

If future engine use proves that a better direction exists, revise:
1. the decision log
2. the affected system docs
3. this accepted-decisions document
