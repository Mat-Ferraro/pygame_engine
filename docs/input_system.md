# Input System

## Purpose

The input system translates raw pygame input into engine-friendly runtime input state and higher-level actions.

Its goals are:
- reduce repetitive raw pygame input handling
- support consistent action-based input
- keep mouse and keyboard behavior predictable
- integrate cleanly with scenes and widgets

---

## Accepted Core Decisions

The input system currently assumes:

- action-based input is preferred over scattered raw key handling
- `handle_event(event) -> bool` is the event-consumption model for scenes and widgets
- input routing should prioritize topmost/modal UI before lower-level scene logic
- debug tools should be supported through explicit input actions, not random hardcoded keys

---

## Current Input Modules

The input package currently contains:

- `actions.py`
- `bindings.py`
- `input_manager.py`

Suggested responsibilities:
- `actions.py` = canonical action identifiers
- `bindings.py` = default mappings from keys/buttons to actions
- `input_manager.py` = current frame input state and query API

---

## Design Principles

1. Raw pygame input still exists, but should be wrapped for convenience.
2. Scenes and widgets should usually query actions or current input state, not manually track transitions themselves.
3. Input handling should support both direct event routing and frame-state queries.
4. UI and gameplay input should remain separable.

---

## Input Layers

### Raw Input
Direct pygame events:
- keydown
- keyup
- mouse motion
- mouse button down
- mouse button up
- wheel input
- text input if added later

### Normalized Runtime State
The engine should track:
- pressed this frame
- released this frame
- held/down
- mouse position
- mouse delta
- wheel delta

### Action Mapping
Game/app code should often work in terms of actions:
- `confirm`
- `cancel`
- `up`
- `down`
- `left`
- `right`
- `pause`
- `debug_toggle`

This decouples behavior from physical keys.

---

## Input Routing Priority

Accepted routing philosophy:

1. application-level essential handling
2. topmost/modal scene or overlay
3. focused widget / UI layer
4. scene-level logic
5. global debug/runtime shortcuts

Exact implementation may vary, but this ordering is the intended direction.

---

## Actions

`actions.py` should define canonical action names or constants.

Recommended rule:
- action names represent intent, not device details

Good examples:
- `CONFIRM`
- `CANCEL`
- `NAV_UP`
- `NAV_DOWN`
- `PAUSE`
- `DEBUG_TOGGLE`

Avoid:
- `ENTER_KEY`
- `ESCAPE_KEY`
- `LEFT_MOUSE_BUTTON`

Those belong to bindings, not actions.

---

## Bindings

`bindings.py` should define the default mapping from physical input to actions.

Examples:
- Enter -> confirm
- Escape -> cancel
- W / Up Arrow -> nav_up
- Mouse Left -> primary_click

Recommended rule:
- bindings are data/config-like
- action definitions remain separate from the mapping

Future possibility:
- allow user overrides or project-specific binding sets

---

## InputManager Responsibilities

`InputManager` should:
- collect raw input state each frame
- track transitions such as just-pressed and just-released
- expose mouse position and related state
- answer action queries
- clear one-frame transient state between frames

It should not:
- contain game behavior
- directly manage scene flow
- become the sole source of all UI logic

---

## Frame Semantics

The input system should define exact meaning for each state:

- **pressed**: became active this frame
- **released**: stopped being active this frame
- **held** / **down**: currently active

This distinction must be stable and documented because many systems depend on it.

---

## Mouse Support

The engine should support:
- current mouse position
- optional previous mouse position
- delta movement
- button pressed/released/down
- wheel delta
- basic hit-test friendliness for widgets

---

## Keyboard Support

The engine should support:
- raw key state queries
- mapped action state queries
- modifier state if needed later
- optional repeat behavior handling

Future possibility:
- text input mode separate from command input mode

---

## Focus and Input

UI focus interacts with input routing.

Recommended rule:
- focused widgets may consume keyboard input first within the active/top UI layer
- mouse-hit widgets may consume pointer input
- scenes should not blindly process UI-consumed input

This is one reason event-consumption support is important.

---

## Input API Direction

Possible runtime queries:

- `is_action_down(action)`
- `was_action_pressed(action)`
- `was_action_released(action)`
- `is_key_down(key)`
- `was_mouse_pressed(button)`
- `get_mouse_pos()`

The exact API can evolve, but these use cases should be supported.

---

## Rebinding

Not required in the first version, but the system should not block it.

Recommended design direction:
- keep actions and bindings separate now
- allow bindings to become data-driven later

---

## Debug Input

Reserved debug actions should be defined explicitly.

Examples:
- debug overlay toggle
- inspector toggle
- console toggle

These should not be scattered as random hardcoded keys.

---

## Rules for Future Development

1. Keep actions separate from physical keys.
2. Keep scene and widget input routing explicit.
3. Keep one-frame transitions accurate and well tested.
4. Avoid duplicating input edge detection in many modules.
5. Do not hardcode device-specific behavior into high-level systems.

---

## Open Questions

- Should mouse buttons also map into actions, or remain partly separate?
- Should action queries be string-based, enum-based, or constant-based?
- Should text input be supported in the first version?
- Should `InputManager` process events directly or consume already-polled event lists?
