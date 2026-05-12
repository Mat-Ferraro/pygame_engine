# Scene Lifecycle

## Purpose

Scenes define high-level application flow such as menus, gameplay screens, editors, overlays, and modal layers.

The scene system should support:
- clean scene switching
- layered overlays
- predictable setup and teardown
- update and draw separation
- event consumption
- optional scene-owned UI roots

---

## Accepted Core Decisions

The scene system currently assumes:

- the runtime model is **stack-based**
- `handle_event(event) -> bool`
- scenes may optionally own a `root_widget`
- stack behavior is preferred over a replace-only scene model
- scenes should support blocking policies rather than a single vague overlay flag

---

## Core Scene Contract

Every scene should support these operations:

- `on_enter()`
- `on_exit()`
- `on_pause()`
- `on_resume()`
- `handle_event(event) -> bool`
- `update(dt)`
- `render(surface)`

Optional but strongly recommended scene properties:
- `root_widget`
- `blocks_update_below`
- `blocks_render_below`
- `blocks_input_below`

---

## Lifecycle Hooks

### `on_enter()`
Called when the scene becomes active.

Use it for:
- initializing runtime-only state
- starting animations
- refreshing cached references
- subscribing to events if scene-local subscriptions exist

### `on_exit()`
Called when the scene is being removed or replaced.

Use it for:
- unsubscribing from events
- releasing temporary resources
- clearing transient state

### `on_pause()`
Called when another scene is pushed on top of this one.

Use it for:
- pausing input-sensitive behavior
- pausing timers or animation if appropriate
- suspending scene-local activity that should not continue under an overlay

### `on_resume()`
Called when a paused scene becomes active again.

Use it for:
- resuming timers
- refreshing input state assumptions
- restarting visual focus indicators if needed

### `handle_event(event) -> bool`
Receives raw pygame events routed to the active scene.

Responsibilities:
- process scene-level event behavior
- optionally pass events to the root widget
- consume events when appropriate

Return value:
- `True` = event consumed
- `False` = event not consumed

### `update(dt)`
Called once per frame with delta time.

Responsibilities:
- advance scene-local state
- update root widget if present
- update scene-local animations, timers, and effects
- avoid direct drawing work here

### `render(surface)`
Called once per frame to draw the scene.

Responsibilities:
- draw background
- draw scene content
- draw root widget if present
- optionally draw scene-local overlays

---

## Scene and Root Widget Relationship

Accepted direction:
- scenes may own an optional `root_widget`
- scenes handle flow and orchestration
- widgets handle detailed UI behavior

Recommended pattern:
- scene receives events first at a high level
- scene may forward to root widget as appropriate
- root widget may consume UI-specific input
- scene may still handle non-UI runtime behavior

This keeps scenes from becoming bloated UI containers.

---

## Scene Flow Models

### Replace flow
One scene replaces another.
Examples:
- main menu -> settings
- loading -> gameplay

### Stack flow
One scene is pushed on top of another.
Examples:
- gameplay + pause menu
- settings dialog over main menu
- debug overlay over gameplay

Accepted design direction:
- stack is the underlying runtime model
- replace is a convenience operation built on that model

---

## Blocking Policy

Instead of using one vague `is_overlay` flag, scenes should support specific blocking behavior.

Recommended flags:
- `blocks_update_below`
- `blocks_render_below`
- `blocks_input_below`

This makes scene stacking behavior much clearer.

Examples:
- a pause menu may block input below, but still allow rendering below
- a loading screen may block update, render, and input below
- a transparent debug overlay may not block render below

---

## SceneManager Responsibilities

`SceneManager` should:
- coordinate scene flow
- set the active root scene
- replace scenes cleanly
- coordinate transitions
- own or coordinate the scene stack policy

It should not:
- contain game-specific logic
- contain widget logic
- become a general state store

---

## SceneStack Responsibilities

`SceneStack` should:
- push scenes
- pop scenes
- expose the active/top scene
- pause and resume scenes as stack depth changes
- support blocking policy during input/update/render traversal

Suggested behavior:
- input routes from top downward until consumed or blocked
- update traverses downward until blocked
- render traverses upward from the lowest visible scene

---

## Transition Behavior

Transitions should be handled separately from scene logic where possible.

Examples:
- fade in
- fade out
- slide
- crossfade

Scenes should not need to implement transition math directly unless they have special custom behavior.

---

## Recommended Rules

1. Keep scenes focused on flow, not low-level layout math.
2. Keep gameplay logic outside scenes when possible.
3. Let scenes coordinate widgets, not become giant widget classes.
4. Keep scene transitions external to the core scene contract.
5. Avoid storing permanent global data directly inside scenes.

---

## Open Questions

- Should `handle_event` first route to the scene or to the root widget by default?
- Should scenes have explicit transparency metadata in addition to block flags?
- Should transition objects be scene-owned or manager-owned?
