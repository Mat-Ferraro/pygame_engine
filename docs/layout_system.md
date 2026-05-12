# Layout System

## Purpose

The layout system controls how widgets are positioned and sized.

Its goals are:
- reduce manual rect math
- make UI composition more predictable
- support reusable layout patterns
- stay simple enough for pygame-style workflows

---

## Accepted Core Decisions

The layout system currently assumes:

- version one layout uses assigned rects and simple helpers
- advanced measurement/layout is deferred
- layout should still be designed so future expansion remains possible
- container widgets may use layout helpers internally

---

## Current Layout Modules

The layout package currently contains:

- `row.py`
- `column.py`
- `grid.py`
- `anchor.py`

These represent the initial layout vocabulary of the engine.

---

## Design Principles

1. Layout logic should be separate from widget drawing logic.
2. Widgets should accept assigned bounds rather than invent all placement themselves.
3. Layout helpers should be composable.
4. Layout should stay understandable without requiring a full retained UI tree measurement engine.

---

## Core Responsibility Split

### Layout system
Responsible for:
- computing positions and sizes
- applying padding, spacing, and alignment
- distributing available space

### Widgets
Responsible for:
- accepting final rects
- rendering within their bounds
- optionally exposing sizing hints later

This split should remain clear.

---

## Current Layout Types

### Row
Arranges children horizontally.

Should support:
- spacing
- padding
- alignment
- fixed and flexible sizing if added later

### Column
Arranges children vertically.

Should support:
- spacing
- padding
- alignment
- fixed and flexible sizing if added later

### Grid
Arranges children in rows and columns.

Should support:
- cell sizing rules
- spacing
- padding
- optional alignment per cell if needed later

### Anchor
Places content relative to a reference rect or screen area.

Useful for:
- corners
- center alignment
- HUD placement
- overlays

---

## Version One Scope

Version one should support:
- assigned rects
- padding
- spacing
- basic alignment
- predictable row/column/grid/anchor behavior

Version one should **not** try to deliver:
- full intrinsic measurement
- advanced shrink/grow negotiation
- full flexbox-like behavior
- broad automatic layout inference

---

## Future Expansion Direction

Although advanced layout is not part of version one, the system should be designed so it can grow later.

Possible future additions:
- `measure(available_size)`
- preferred size
- minimum size
- fill/stretch weights
- wrap behavior
- more advanced grid sizing rules

Accepted rule:
- leave room for expansion, but do not implement it prematurely

---

## Possible Layout Inputs

Layout helpers may need:
- parent bounds
- child count
- spacing
- padding
- alignment flags
- min/preferred size hints later

For version one, parent-bounds-in / assigned-rects-out is enough.

---

## Padding and Spacing

These must be defined clearly because layout bugs often come from inconsistent interpretation.

### Padding
Space inside a layout container between the container edge and content.

### Spacing
Space between child items.

Padding and spacing should never be conflated.

---

## Alignment

Alignment should define how children sit within available space.

Potential options:
- start
- center
- end
- stretch

Recommended rule:
- keep alignment names explicit and shared across layout types where possible

---

## Clipping

Recommended rule:
- clipping should usually be widget/container-owned
- layout decides bounds, widget decides whether to clip during render

---

## Layout and UI Containers

Container widgets like `Panel` and `Stack` may use layout helpers internally.

Recommended rule:
- container widgets may own a layout helper
- layout helpers should remain reusable outside any one widget class

---

## Absolute vs Managed Layout

The engine should support both:
- absolute/manual placement for simple cases
- managed layout for reusable compositions

Not every widget must use a layout helper.

---

## Rules for Future Development

1. Keep layout math separate from widget drawing.
2. Keep first-version layout simple.
3. Prefer clear rect assignment over magic resizing rules.
4. Add measurement only when real use cases demand it.
5. Keep row/column/grid/anchor semantics consistent.

---

## Open Questions

- Should widgets expose `get_min_size()` in version one?
- Should fill/stretch behavior exist immediately?
- Should layout objects be stateless helpers or stateful instances?
- Should grid support mixed fixed and weighted columns early on?
