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

Every widget should support:
- `handle_event(event) -> bool`
- `update(dt)`
- `render(surface)`
- `set_rect(rect)`

Common state fields:
- `rect`
- `visible`
- `enabled`
- `hovered`
- `focused`

Container widgets may additionally maintain:
- `children`
- clipping behavior
- focus traversal support

---

## Base Widget vs Container Widgets

### Base `Widget`
Provides:
- local state
- event/update/render contract
- assigned rect support

Does **not** provide:
- generic child list management by default

### Container widgets
Container widgets may provide:
- child ownership
- event routing to children
- child update/render traversal
- optional clipping

Examples:
- `Panel`
- `Stack`

`Panel` is the surfaced container.
`Stack` is the transparent grouping/layering container.

---

## Text widgets

### `Label`
- single-line
- cached text surface
- simple alignment

### `TextBlock`
- multi-line
- wrapped to available width
- cached text surface
- line spacing and padding support

Text widgets remain presentation widgets, not general containers.

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

## Locked Implementation Decisions

### Theme access is globally resolved, not injected
**Decision:** Widgets call `get_theme()` from `theme/runtime.py`.

### No keyboard navigation in the base layer
**Decision:** `focused` exists on `Widget`, but focus traversal belongs in
containers.

### `_handle_event_widget` is the override point
**Decision:** Subclasses override `_handle_event_widget` rather than
`handle_event` directly when they want to keep standard guards.

### `visible=False` skips everything; `enabled=False` skips events only
**Decision:** Invisible widgets skip event, update, and render work. Disabled
widgets still render and update but do not process events.

### No measurement API in v1
**Decision:** `set_rect(rect)` is the only required layout interface for now.
