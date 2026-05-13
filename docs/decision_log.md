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

---

#### Stack-based scene model
**Decision:** The runtime uses a `SceneStack`. `SceneManager` coordinates it.
Scene replacement is a convenience wrapper over push/pop.

**Reason:** Overlays, pause menus, and modal dialogs require layered scene
rendering and input blocking. A flat single-scene model can't represent these
cleanly.

---

#### `handle_event` returns `bool`
**Decision:** Scene and widget `handle_event` methods return `True` (consumed)
or `False` (not consumed).

**Reason:** This is the correct signal for layered input routing. Without
consumption signals, every layer processes every event regardless of whether a
layer above already handled it.

---

#### Widget base does not own children
**Decision:** The base `Widget` class does not automatically manage child
widgets. Child management belongs to container subclasses.

**Reason:** A base that auto-manages children forces complexity on widgets that
don't need it. Containers opt into that behavior explicitly.

---

#### Composition over inheritance for UI
**Decision:** Larger UI pieces should be built from smaller widgets and
containers rather than through deep inheritance hierarchies.

**Reason:** Deep inheritance makes behavior harder to trace and widgets harder
to reuse independently.

---

#### Action/binding split in input
**Decision:** `actions.py` defines intent-based action names. `bindings.py`
maps physical keys to those actions. `InputManager` resolves queries against
the bound state.

**Reason:** Decouples game/engine behavior from physical device details. Makes
rebinding possible without touching any game logic.

---

#### Asset loading: lazy + cached, fail loudly
**Decision:** Assets are loaded on first request and cached. Missing assets
raise clear errors during development.

**Reason:** Lazy loading avoids unnecessary startup cost. Hard failure during
development prevents silent broken-asset bugs.

---

#### Theme: tokens → defaults → runtime
**Decision:** Raw design values live in `tokens.py`. A baseline theme is
assembled in `defaults.py`. The active theme is accessed through `runtime.py`.

**Reason:** Separates raw values from assembled themes from runtime access.
Allows projects to override at any layer without touching widget logic.

---

#### Persistence: engine owns infrastructure, game owns schema
**Decision:** The engine provides save slot management, safe file I/O,
versioning, and migration hooks. The consuming game defines the save payload
and its meaning.

**Reason:** Persistence infrastructure is generic and reusable. The save schema
is inherently game-specific and has no place in the engine.

---

#### State: engine state only, no game domain state
**Decision:** The `state/` package holds engine-level runtime state only (debug
flags, theme name, etc.). Game-specific state belongs in the consuming project.

**Reason:** Mixing game state into the engine couples the engine to specific
games and makes it non-reusable.

---

### Infrastructure decisions

#### Repository layout: docs/examples/tests at repo root
**Decision:** `docs/`, `examples/`, and `tests/` live at the **repo root**,
not inside the `pygame_engine/` importable package.

**Reason:** Developer tooling, documentation, and test code should not be part
of the installed package. Placing them inside the package tree pollutes the
import namespace and ships unnecessary files to consumers. Standard Python
convention (PEP 517 / setuptools) is to keep source under a named package
directory with tooling alongside it.

---

#### Headless pygame in tests via conftest.py
**Decision:** `tests/conftest.py` provides a session-scoped `pygame_init`
fixture that initialises pygame without opening a display window.

**Reason:** Tests that touch pygame primitives (`Rect`, `Surface`, etc.) would
crash without initialisation. A shared session fixture avoids duplicating this
setup across test files and makes the suite runnable in headless CI
environments.

---

#### pyproject.toml as single build/tool config
**Decision:** All build configuration, dependency declarations, pytest config,
and mypy config live in `pyproject.toml`. No `setup.py`, `setup.cfg`, or
separate `pytest.ini`/`mypy.ini` files.

**Reason:** Single source of truth for project tooling. PEP 517 standard.

---

### Application implementation — initial pass

#### Single `run(initial_scene)` entry point
**Decision:** `Application.__init__()` is side-effect-free. All pygame
initialisation happens inside `run()`, which calls `_startup()`, then
`_loop()`, then guarantees `_shutdown()` via a `finally` block.

**Reason:** Construction should be cheap and safe to call in tests or tooling
without opening a window. One entry point is simpler than a `start()` / `run()`
split with no concrete reason to split them.

---

#### `Application` owns `InputManager`
**Decision:** `Application` constructs and owns `InputManager` during
`_startup()`. It is not injected from outside.

**Reason:** Injection adds complexity with no benefit in a personal framework
that has no plugin or multi-app requirements.

---

#### dt clamping via `AppConfig.max_dt`
**Decision:** Delta time is clamped to `config.max_dt` (default 0.1 s) each
frame. Clamping is disabled by setting `max_dt = 0`.

**Reason:** Without clamping, pausing in a debugger or moving the window
produces a massive dt spike that breaks physics and animations. A small default
clamp is almost always the right choice.

---

#### Frame loop order is locked
**Decision:** The frame loop follows this fixed order:
poll events → update input → route events → update scenes → update debug →
clear → render scenes → render debug → flip → tick clock / compute dt.

**Reason:** This order is documented in `application_contract.md`. Locking it
now prevents gradual drift across future edits. Changes to the order require
updating both the code and the doc.

---

### Scene system — initial pass

#### Root widget gets first refusal on events
**Decision:** `Scene.handle_event` passes the event to `root_widget` first.
Scene-level logic is in `_handle_event_scene`, called only if the widget does
not consume the event.

**Reason:** UI should always handle its own input before scene logic sees it.
A button click should not also trigger scene-level behavior.

#### SceneStack owns traversal; SceneManager owns lifecycle
**Decision:** Split responsibilities cleanly — `SceneStack` handles frame
traversal and blocking policy. `SceneManager` handles all lifecycle hook
calls. Neither does the other's job.

**Reason:** Mixing lifecycle and traversal logic in one class makes both
harder to reason about and test independently.

#### Transitions deferred
**Decision:** `transitions.py` is a documented stub. Not implemented in v1
spine pass.

**Reason:** Transitions are a polish concern. Getting the core
Application → Scene → Widget → SceneManager chain working and tested first
avoids building polish on an unstable foundation.

---

### Widget base — initial pass

#### Theme access: globally resolved
**Decision:** Widgets call `get_active_theme()` from `theme/runtime.py`.
Not injected at construction.

**Reason:** Injection adds ceremony at every call site in a framework where
all consumers are controlled. One stable global accessor is simpler.

#### No keyboard navigation in the base
**Decision:** `focused` flag exists; traversal logic belongs in containers.

**Reason:** Focus traversal is a container concern. The base widget handles
keyboard input when focused but does not decide which widget is focused.

#### `_handle_event_widget` is the subclass override point
**Decision:** `handle_event` owns guards and hover. Subclasses override
`_handle_event_widget` to add interaction logic without re-implementing guards.

#### Widget wired into Scene
**Decision:** `Scene.root_widget` is now typed as `Widget | None`. All three
frame methods (`handle_event`, `update`, `render`) delegate to `root_widget`
with real calls rather than TODO stubs.

---

### Input system — initial pass

#### Actions are plain string constants
**Decision:** Module-level string constants in `actions.py`. No enum.
**Reason:** Simple to extend per-project, no import overhead.

#### Mouse buttons stay off the action system
**Decision:** Direct queries only (`was_mouse_pressed`, `get_mouse_pos`).
**Reason:** Widgets need the position for hit-testing regardless; routing
mouse through actions adds a layer with no benefit.

#### Text input deferred
**Decision:** Not in v1. Flagged for later.
**Reason:** Distinct mode that warrants its own design when a real use case
drives it.

#### `update(events)` receives the polled list from Application
**Decision:** Application polls once, passes the list to InputManager and
the event routing loop.
**Reason:** No double-polling; single source of truth for the frame's events.

---

### Layout system — initial pass

#### Stateless functions
**Decision:** `row`, `column`, `grid`, `anchor` are plain functions.
**Reason:** No lifecycle, trivially composable and testable.

#### Uniform grid cells in v1
**Decision:** All grid cells the same size. Mixed sizing deferred.
**Reason:** Covers v1 needs; mixed sizing adds complexity for no immediate gain.

#### No measurement API in v1
**Decision:** No `get_min_size()` or `measure()`. Layout takes explicit sizes.
**Reason:** Measurement needs font/theme access. Deferred until those exist.

---

### Button and Label — initial pass

#### Label caches its rendered surface with a dirty flag
**Decision:** Label renders text to a `pygame.Surface` once and caches it.
The cache is invalidated (dirty=True) when `text`, `colour`, or `rect` changes.

**Reason:** `font.render()` is not free. Calling it every frame for every
label on screen wastes CPU. The dirty flag keeps updates correct without
re-rendering unnecessarily.

#### Button uses an internal Label for text
**Decision:** `Button` owns a `Label` instance for its text. It does not
call `font.render()` directly.

**Reason:** Reuses Label's caching, alignment, and future theme integration
without duplicating text rendering logic.

#### Button click semantics: press inside + release inside
**Decision:** `on_click` fires only when mouse button is pressed inside the
button rect AND released inside it. Releasing outside after pressing inside
cancels the click.

**Reason:** Standard button click semantics. Prevents accidental clicks when
the user drags away after pressing.

#### Colours are class-level constants for now
**Decision:** Button and Label use explicit colour arguments / class-level
colour constants. Theme lookup is noted as a future step in both docstrings.

**Reason:** Theme system doesn't exist yet. Hardcoded defaults with a clear
upgrade path is better than blocking widget development on theme.

---

### Theme system — initial pass

#### Dataclasses for theme objects
**Decision:** `Theme` and sub-objects are `@dataclass` instances.
**Reason:** Dot-access, autocomplete, type safety. No boilerplate. Override
via `dataclasses.replace()`.

#### Module-level accessor pattern
**Decision:** `get_theme()` / `set_theme()` in `runtime.py`. No injection.
**Reason:** Injection adds friction at every call site in a controlled codebase.

#### No widget-level theme caching
**Decision:** Widgets call `get_theme()` each frame.
**Reason:** Attribute lookup is free. Caching adds complexity for nothing.

#### Widget hardcoded colours replaced
**Decision:** `Button` and `Label` now read all colour/size values from
`get_theme()`. Class-level colour constants removed from `Button`.
`Label` uses `_UNSET` sentinel to distinguish "not supplied" from explicit
`None`, falling back to theme values when not supplied.

---

### Panel and utils — initial pass

#### Panel owns a child list, not a layout helper
**Decision:** Panel manages children and handles traversal. Layout is
applied externally via layout helpers before adding children.
**Reason:** Keeps Panel focused on containment. Layout and containment
are separate concerns — mixing them would make Panel harder to reuse.

#### Panel event routing is reverse add-order
**Decision:** Events route through children in reverse add-order (last
added = topmost = first to receive events). Rendering is forward add-order.
**Reason:** Last-added widgets visually sit on top; they should also have
first refusal on input. This matches standard UI layering expectations.

#### Panel clipping is opt-in via `clip=True`
**Decision:** Clipping is off by default. Pass `clip=True` to scissor
child rendering to the panel rect.
**Reason:** Most panels don't need clipping and it has a small cost.
Scrollable containers and overflow cases opt in explicitly.

#### utils modules are pure functions / classes with no engine dependencies
**Decision:** `timers.py`, `colors.py`, `rects.py`, `mathx.py` have no
imports from the rest of `pygame_engine`. They are standalone utilities.
**Reason:** Utils should be the lowest layer — nothing else should depend
on them, and they should never create circular imports.

---

### Toast and Tooltip — initial pass

#### Tooltip position is driven externally each frame
**Decision:** The caller calls `tooltip.show(mouse_pos)` every frame the
tooltip should be visible. Tooltip does not subscribe to mouse events itself.
**Reason:** Keeps Tooltip decoupled from the input system. The caller
already knows the mouse position; passing it in is one line.

#### Tooltip renders nothing when not visible — render it last
**Decision:** Tooltip.render() is a no-op when hidden. The caller is
responsible for rendering it after all other widgets.
**Reason:** Tooltips must appear on top of everything. The cleanest way to
guarantee that is for the scene to render them last, not for the tooltip to
try to manage its own z-order.

#### Toast manages its own lifecycle via Timer phases
**Decision:** Toast cycles through idle → fade_in → hold → fade_out →
expired using a `Timer` per phase. The caller checks `is_expired` each
frame and removes/recycles the toast when True.
**Reason:** Self-contained lifecycle means the caller only has to call
`show()` once and `update(dt)` each frame. No external timer management needed.

#### Toast kind controls accent colour only
**Decision:** `kind` ("info", "success", "warning", "error") changes the
left accent bar colour. Background and text colours come from the theme.
**Reason:** Semantic colour tinting with a consistent visual style. Full
per-kind theme entries are a future addition if needed.

#### Toast and Tooltip rendered manually outside the widget tree
**Decision:** In examples and typical usage, Toast and Tooltip are updated
and rendered by the scene directly, not added to a Panel or Stack.
**Reason:** They must always appear on top. Adding them to the widget tree
would require z-ordering support that doesn't exist yet. Manual rendering
last guarantees correct layering with no infrastructure needed.
