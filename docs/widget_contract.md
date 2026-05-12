## Purpose

Widgets are reusable UI building blocks used across scenes.

They should be:
- composable
- lightweight
- predictable
- independent from game-specific logic

---

## Accepted Core Decisions

The widget system currently assumes:

- `handle_event(event) -> bool`
- base `Widget` does **not** automatically manage children
- child-management belongs to container widgets
- widgets may access styling through a stable runtime theme interface
- layout version one uses assigned rects and simple layout helpers

---

## Core Widget Responsibilities

A widget may:
- receive events
- update internal state
- render itself
- participate in layout
- expose visible/enabled/focused/hovered state

A widget should not:
- know about game-specific systems
- directly own scene flow
- automatically become a container unless it is specifically a container widget
- load large assets on demand during normal frame updates

---

## Baseline Widget Interface

Every widget should support the following core behavior:

- `handle_event(event) -> bool`
- `update(dt)`
- `render(surface)`
- `set_rect(rect)` or equivalent layout assignment
- visibility/enabled state

Common state fields:
- `rect`
- `visible`
- `enabled`
- `hovered`
- `focused`

Container widgets may additionally maintain:
- `children`
- layout rules
- clipping behavior
- focus traversal support

---

## Event Handling

### `handle_event(event) -> bool`
Receives raw pygame events or framework-routed events.

A widget may:
- respond to pointer input
- respond to keyboard input if focused
- consume events when appropriate

Return value:
- `True` = event consumed
- `False` = event not consumed

Container widgets may additionally:
- route events to children
- stop propagation when a child consumes input

This event-consumption model is an accepted engine decision.

---

## Update

### `update(dt)`
Used for:
- animations
- timers
- hover/focus transitions
- state cleanup

Container widgets may also update children.

Avoid:
- expensive asset loading
- direct scene management
- unrelated global state mutation

---

## Render

### `render(surface)`
Responsible for drawing the widget onto a provided surface.

A widget should:
- respect its `rect`
- skip rendering when not visible

Container widgets may also:
- render children
- apply clipping
- draw backgrounds/borders before children
- draw overlays after children

---

## Layout

Accepted version one direction:
- layout helpers compute rects
- widgets accept final assigned bounds
- advanced measurement is not required in v1

Possible initial API:
- `set_rect(rect)`

Possible future additions:
- `measure(available_size)`
- `get_min_size()`
- preferred size hints

The engine should leave room for layout expansion later, but not implement the full advanced model now.

---

## Focus and Interaction State

Widgets may support:
- hover state
- pressed state
- focused state
- disabled state

Interactive widgets should behave consistently:
- disabled widgets do not process interactions
- invisible widgets do not process interactions
- focused widgets may react to keyboard input
- hover should depend on pointer hit-testing

---

## Base Widget vs Container Widgets

This distinction is important.

### Base `Widget`
Should provide:
- local state
- event/update/render contract
- assigned rect support
- theme-aware styling access if needed

Should **not** provide:
- generic child list management by default

### Container Widgets
Container widgets may provide:
- child ownership
- event routing to children
- child update/render traversal
- layout support
- clipping

Examples:
- `Panel`
- `Stack`

This is an accepted engine direction.

---

## Control Widgets

Control widgets should:
- expose callbacks or signals
- stay small and focused
- avoid embedding unrelated layout behavior

Examples:
- `Button`
- `Dropdown`

---

## Text Widgets

Text widgets should focus on presentation and measurement.

Examples:
- `Label`
- `TextBlock`

They should not become general containers unless clearly needed.

---

## Feedback Widgets

Short-lived or reactive widgets belong in the feedback category.

Examples:
- `Toast`
- `Tooltip`

These may have additional timing and layering behavior.

---

## Theme Relationship

Accepted direction:
- widgets may access style data through a stable runtime theme interface
- widgets should not hardcode visual constants throughout their implementation
- local style overrides may be added later

---

## Recommended Rules

1. Keep widgets reusable and game-agnostic.
2. Keep drawing, event handling, and update behavior separate.
3. Prefer composition over deep inheritance.
4. Keep container responsibilities distinct from control responsibilities.
5. Avoid bloated base widget classes.

---

## Open Questions

- How much keyboard-navigation support belongs in the base layer?
- Should theme access be injected or globally resolved at runtime?
- When should measurement APIs be added beyond assigned rects?

---

## Locked Implementation Decisions

### Theme access is globally resolved, not injected
**Decision:** Widgets call `get_active_theme()` from `theme/runtime.py` when
they need style data. Theme is not passed at widget construction.

**Reason:** Injection at every widget constructor call adds significant
ceremony with no concrete benefit in a personal framework where all call sites
are controlled. A single stable global accessor in `theme/runtime.py` keeps it
swappable without the verbosity.

### No keyboard navigation in the base layer
**Decision:** `focused` state exists on `Widget` so the infrastructure is
present, but focus traversal logic belongs in container widgets. The base
widget only responds to keyboard events when `focused = True` — it does not
manage which widget is focused or how focus moves between widgets.

**Reason:** Focus traversal is a container-level concern. Adding it to the
base widget would bloat every widget with behavior most won't use.

### `_handle_event_widget` is the override point, not `handle_event`
**Decision:** Subclasses override `_handle_event_widget` rather than
`handle_event` directly. `handle_event` owns the visibility/enabled guards and
hover update, so overriding it directly would require every subclass to
re-implement those guards.

### Hover is updated before the enabled check
**Decision:** `handle_event` updates `hovered` via MOUSEMOTION before
checking `enabled`. A disabled widget still tracks hover so it can show a
correct visual state (e.g. a not-allowed cursor style) without processing
any actual interaction.

### `visible=False` skips everything; `enabled=False` skips events only
**Decision:** A non-visible widget returns False from `handle_event`
immediately and its `render` and `update` are no-ops. A non-enabled widget
still renders and updates (so animations continue) but does not process events.

### No measurement API in v1
**Decision:** `set_rect(rect)` is the only layout interface on `Widget`.
`measure()` and `get_min_size()` are noted as future additions in the contract
doc but are not implemented. Layout helpers assign rects directly.
