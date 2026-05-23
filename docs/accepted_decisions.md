> **Note**
> This document records architecture decisions made during v1.x development.
> For the current authoritative architecture, see `DESIGN_SPEC.md`.
> For the current enforceable restrictions, see `RESTRICTIONS.md`.
> Some decisions here (notably #10 Theme Access, #15 Version One Boundary)
> have been superseded by the v2.0 design work documented in `DESIGN_SPEC.md`.

---

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

---

### 18. Game Project Template
A `game_template/` directory lives at the repo root alongside `pygame_engine/`.
It is an immediately runnable skeleton that all future game projects start from.

It provides: wired `main.py`, working main menu, stub game/pause/settings scenes,
`game/actions.py` for combined engine+game actions, documented stub packages for
models/systems/ui, and a README explaining the development workflow.

**Rule:** copy `game_template/`, rename `MY_GAME`, run `python main.py`.

---

### 19. EventBus and Signals
The `events/` package provides pub/sub event messaging for loose coupling
between game systems.

- `EventBus` — synchronous pub/sub with wildcard patterns, one-shot subscriptions,
  and broken-handler isolation. Module-level `bus` singleton.
- `Signal` — typed wrapper around a specific EventBus event for cleaner APIs.

Use `EventBus` for discrete game events ("player.damaged", "item.collected").
Use `Observable` for reactive values (a health float that the HUD watches).
These are complementary, not redundant.

---

### 20. StateStore Not Implemented
`state/state_store.py` has been deleted. No generic key-value state store
is implemented.

`Observable` covers reactive state. `RuntimeFlags` covers engine boolean flags.
A generic store has no concrete use case and creates dumping-ground risk.

---

### 21. Scene Transitions Are Opt-In
`push`, `replace`, `pop`, and `clear_and_push` on `SceneManager` remain
unchanged and transition-free.

Transitions are opt-in via `push_with`, `replace_with`, and `pop_with`.
Passing no transition is always valid and has zero overhead.

---

### 22. Physics Is Out of Scope
`pygame_engine` will not include a physics engine. See `roadmap.md`.
Games that need physics should use **pymunk** as a game-level dependency.

---

### 23. Scenes Receive Application Directly
Game scenes receive the `Application` instance as a constructor argument
and store it as `self._app`.

```python
class GameScene(Scene):
    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app = app
```

Scenes access services via `self._app.input_manager`, `self._app.assets`,
`self._app.audio`, `self._app.scene_manager`, etc.

**Reason:** A narrower context object was considered but deferred. Direct
app access is simple, explicit, and sufficient for the current scope. If
coupling becomes a problem across many game projects, a `SceneContext`
wrapper can be introduced without breaking existing scenes.

**Rule:** Scenes use `self._app` for cross-cutting services. They do not
import `Application` as a global or use module-level singletons for
services (other than `bus` and `flags` which are intentionally global).

---

### 24. Scene overlay_render Pass
`Scene.render()` calls `overlay_render(surface)` as a second pass after
the main widget tree render.

Scenes that use `Dropdown` or floating `Tooltip` widgets override
`overlay_render()` to render those widgets last, ensuring they appear
above all other content:

```python
def overlay_render(self, surface):
    self._resolution_dropdown.overlay_render(surface)
```

Default implementation is a no-op. Scenes that do not use floating
widgets do not need to override it.

---

### 25. Scene Descriptor Is the Source of Truth for UI Layout

A `DescribedScene`'s UI is **authored as data** — a `SceneDescriptor` tree of
`WidgetNode`s — not built imperatively in scene code. The engine realises the
descriptor into the live widget tree; the editor edits the descriptor; the
live widgets follow.

**Rationale.** The engine previously held two unreconciled models of a
scene's UI: the live widget tree (what rendered) and the `SceneDescriptor`
(what the editor inspected). Nothing connected them, leaving the
`layout_builder` DSL, the `WidgetNode` prefab fields, and `.layout.json`
persistence built but unused. This decision makes the descriptor the single
model and removes that redundancy.

**Mechanism.**

- `pygame_engine/ui/widget_registry.py` — the single source of truth for
  which widget types exist and how each is constructed from a `WidgetNode`.
  Built-in types self-register; games register custom types with
  `@register(...)`. An unknown type raises, never silently no-ops.
- `pygame_engine/scene/layout_loader.py` — `LayoutLoader` walks a descriptor,
  builds the widget tree via the registry, and subscribes each widget's rect
  to its `node.rect` so descriptor edits move the live widget.
- `DescribedScene.on_enter()` runs `_build_layout()` → `LayoutLoader` →
  assigns `root_widget` → `_bind_behavior()`.

**Layout vs behaviour.** The descriptor stores structure and geometry only,
so it stays JSON-serialisable. Behaviour — `on_click` handlers, navigation —
is **not** stored in the descriptor. Scenes attach it in `_bind_behavior()`
after the widgets exist, by looking widgets up via `widget_id`.

**Re-runnable layout.** `_build_layout()` must be safe to call repeatedly: it
runs on enter and again on every `on_resize()`. The base class clears the
descriptor before each call; subclasses compute geometry against
`self.screen_rect`, which is refreshed on resize.

**Consequence.** Scenes that want descriptor-driven UI subclass
`DescribedScene`; scenes that do not subclass `Scene` directly. Real scenes
migrate to `DescribedScene` over time — `MainMenuScene` was migrated first as
the proving case.

**Deferred.** Storing unresolved anchor/layout specs in the descriptor (so
layouts re-flow without re-running `_build_layout()`) is a future design
effort, not part of this decision. See `docs/sprints/SPRINT_descriptor_authority.md`.
