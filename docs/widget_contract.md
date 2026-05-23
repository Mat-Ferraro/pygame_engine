# pygame_engine — Widget Contract

**Version:** 2.0-design
**Authority:** Practical supplement to ARCHITECTURE.md. The descriptor
section reflects accepted decision #25 (Scene Descriptor Is the Source of
Truth for UI Layout).

---

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

## Widgets and the Scene Descriptor

Per accepted decision #25, a `DescribedScene` authors its UI as a
`SceneDescriptor` and the engine builds the live widgets from it. This
gives every widget *type* a second obligation beyond the runtime contract
above: it must be **constructible from descriptor data**.

### The widget registry

`pygame_engine/ui/widget_registry.py` is the single source of truth for
which widget types exist and how each is built from a `WidgetNode`. It
maps a type string (`"Panel"`, `"Button"`, …) to a *builder function*.

- Built-in engine widgets register their builders automatically when the
  registry module is imported.
- A game's own widget types must be registered explicitly, with the
  `@register("MyType")` decorator (use `container=True` for container
  types so the loader knows to recurse children into them).
- An unregistered type fails **loudly** when a scene loads — it is never
  silently skipped.

### Why builder functions, not bare constructors

Widget constructors are deliberately not uniform — `Button(rect, label,
on_click)` differs from `Label(rect, text, font_size, …)`. A blanket
`cls(rect, **props)` would break the moment a prop name did not match a
constructor parameter. Each type therefore registers a small builder that
knows its own constructor and reads only the props it understands.

### Layout vs behaviour — what a builder may touch

The descriptor stores **structure and geometry only**, so it stays
JSON-serialisable. A builder constructs a widget's layout — its rect and
static props (a Button's `label`, a Label's `text`). It must **not**
expect behaviour: callbacks such as `on_click` are not descriptor data
and are not built here. The owning scene attaches behaviour afterward, by
`widget_id`, in `_bind_behavior()` (see SCENE_AUTHORING_GUIDE.md §12).

### Obligation for new widget types

When you add a new widget type intended for use in `DescribedScene`s:

1. Keep the runtime contract above (the baseline interface, the
   visible/enabled rules, `_handle_event_widget` as the override point).
2. Register a builder with the widget registry.
3. Keep all constructor arguments that a builder needs either
   descriptor-serialisable (numbers, strings, lists) or optional with a
   sane default. Anything that is genuinely behaviour stays out of the
   constructor's required arguments.

A widget type that is only ever built in code (never authored in a
descriptor) does not need a registered builder — but registering one is
cheap and makes the type editor-usable later.

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


### Widget types intended for descriptors must be registered
**Decision:** A widget type used in a `DescribedScene` registers a builder
with `widget_registry`. Type knowledge lives in the registry, never as
type-checks scattered through the layout loader. See "Widgets and the
Scene Descriptor" above.
