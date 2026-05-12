# Decision Log

## Purpose

This log records significant architecture decisions chronologically, including
the reasoning and any alternatives considered.

For the current accepted rule set, see `accepted_decisions.md`.

---

## Decisions

### 2025 — Initial Architecture Phase

#### Engine scope: lightweight framework, not genre engine
**Decision:** `pygame_engine` is a lightweight reusable framework. It does not
contain game-specific hero, combat, inventory, or campaign logic.

**Reason:** A generic foundation is more reusable across future projects. Genre
logic belongs in the consuming game.

#### Stack-based scene model
**Decision:** The runtime uses a `SceneStack`. `SceneManager` coordinates it.
Scene replacement is a convenience wrapper over push/pop.

**Reason:** Overlays, pause menus, and modal dialogs require layered scene
rendering and input blocking. A flat single-scene model cannot represent these
cleanly.

#### `handle_event` returns `bool`
**Decision:** Scene and widget `handle_event` methods return `True` (consumed)
or `False` (not consumed).

**Reason:** This is the correct signal for layered input routing.

#### Widget base does not own children
**Decision:** The base `Widget` class does not automatically manage child
widgets. Child management belongs to container subclasses.

**Reason:** A base that auto-manages children forces complexity on widgets that
do not need it.

#### Composition over inheritance for UI
**Decision:** Larger UI pieces should be built from smaller widgets and
containers rather than through deep inheritance hierarchies.

**Reason:** Deep inheritance makes behavior harder to trace and widgets harder
to reuse independently.

#### Action/binding split in input
**Decision:** `actions.py` defines intent-based action names. `bindings.py`
maps physical keys to those actions. `InputManager` resolves queries against
the bound state.

**Reason:** Decouples engine behavior from physical device details.

#### Asset loading: lazy + cached, fail loudly
**Decision:** Assets are loaded on first request and cached. Missing assets
raise clear errors during development.

**Reason:** Lazy loading avoids unnecessary startup cost. Hard failure prevents
silent broken-asset bugs.

#### Theme: tokens → defaults → runtime
**Decision:** Raw design values live in `tokens.py`. A baseline theme is
assembled in `defaults.py`. The active theme is accessed through `runtime.py`.

**Reason:** Separates raw values from assembled themes from runtime access.

#### Persistence: engine owns infrastructure, game owns schema
**Decision:** The engine provides save slot management, safe file I/O,
versioning, and migration hooks. The consuming game defines the save payload
and its meaning.

**Reason:** Persistence infrastructure is generic and reusable.

#### State: engine state only, no game domain state
**Decision:** The `state/` package holds engine-level runtime state only.
Game-specific state belongs in the consuming project.

**Reason:** Mixing game state into the engine couples the engine to specific
games and makes it less reusable.

### Infrastructure decisions

#### Repository layout: docs/examples/tests at repo root
**Decision:** `docs/`, `examples/`, and `tests/` live at the repo root, not
inside the importable package.

**Reason:** Developer tooling and docs should not ship as installed package
contents.

#### Headless pygame in tests via conftest.py
**Decision:** `tests/conftest.py` provides session-scoped headless pygame
initialisation.

**Reason:** Lets pygame-based tests run in CI without opening a display window.

#### pyproject.toml as single build/tool config
**Decision:** Build config, dependency declarations, pytest config, and type
tooling live in `pyproject.toml`.

**Reason:** Single source of truth.

### Runtime and UI implementation

#### Single `run(initial_scene)` entry point
**Decision:** `Application.__init__()` is side-effect-free. All pygame
initialisation happens inside `run()`.

**Reason:** Construction should be cheap and safe for tests and tooling.

#### `Application` owns `InputManager`
**Decision:** `Application` constructs and owns `InputManager` during startup.

**Reason:** Injection adds complexity with no benefit at this scale.

#### Frame loop order is locked
**Decision:** The frame loop order is fixed and documented.

**Reason:** Prevents drift between implementation and contracts.

#### Root widget gets first refusal on events
**Decision:** `Scene.handle_event` passes the event to `root_widget` first,
then scene-level `_handle_event_scene`.

**Reason:** UI should always handle its own input before scene logic.

#### SceneStack owns traversal; SceneManager owns lifecycle
**Decision:** `SceneStack` handles traversal and blocking policy. `SceneManager`
handles lifecycle hooks.

**Reason:** Clean separation makes both easier to reason about and test.

#### Theme access: globally resolved
**Decision:** Widgets call `get_theme()` from `theme/runtime.py`. Theme is not
injected into each widget.

**Reason:** Simpler call sites and low overhead.

#### No keyboard navigation in the base widget
**Decision:** `focused` exists on `Widget`, but traversal logic belongs in
containers.

**Reason:** Focus movement is a container concern, not a base-widget concern.

#### Stateless layout helpers
**Decision:** `row`, `column`, `grid`, and `anchor` are plain functions.

**Reason:** They are trivially composable and testable.

#### Button click semantics: press inside + release inside
**Decision:** `Button.on_click` fires only when the press and release both occur
inside the button rect.

**Reason:** Standard button behavior and easy cancellation on drag-out.

#### Theme values are dataclasses
**Decision:** Theme objects are dataclasses, not plain dicts.

**Reason:** Dot-access, autocomplete, and clearer typing.

#### Transparent grouping container added
**Decision:** `Stack` is a transparent child-managing container distinct from
`Panel`.

**Reason:** Grouping and z-ordering are useful without always wanting a surfaced
background or border.

#### Wrapped text widget added
**Decision:** `TextBlock` is the multi-line counterpart to `Label`.

**Reason:** Core UI toolkit needed a built-in wrapped text primitive before
moving to more complex widgets like `Dropdown`, `Tooltip`, or `Toast`.
