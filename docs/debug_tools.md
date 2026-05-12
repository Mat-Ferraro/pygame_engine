# Debug Tools

## Purpose

The debug package provides development-time visibility into runtime behavior.

Its role is to help engine and game developers inspect:
- frame timing
- current scene state
- widget layout/bounds
- logs and events
- runtime flags and toggles

It should improve development speed without polluting normal runtime behavior.

---

## Accepted Core Decisions

The debug system currently assumes:

- debug tools are important and should be well supported
- debug tools should remain optional runtime layers, not mandatory core logic
- debug activation should be explicit
- debug input should be action-driven, not hidden behind random hardcoded keys

---

## Current Debug Modules

The debug package currently contains:

- `console.py`
- `debug_log.py`
- `inspector.py`
- `overlay.py`

Suggested responsibilities:
- `console.py` = interactive or on-screen dev console
- `debug_log.py` = debug logging helpers
- `inspector.py` = state/object/widget inspection
- `overlay.py` = visual on-screen debug overlay

---

## Design Principles

1. Debug tools should be easy to disable.
2. Debug tools should not become required for normal runtime behavior.
3. Debug-only visuals and controls should be clearly separated from production UI.
4. Logs and overlays should help diagnose problems, not create new architecture coupling.

---

## Debug Overlay

The overlay may display:
- fps
- frame time
- current scene name
- input state summaries
- widget counts
- bounds overlays
- other lightweight runtime information

Recommended rule:
- overlay drawing should happen after normal scene rendering

---

## Inspector

The inspector is for deeper introspection.

Possible use cases:
- inspect current scene stack
- inspect widget tree
- inspect runtime flags
- inspect layout bounds
- inspect active theme values
- inspect event subscriptions if possible later

Recommended rule:
- inspector should read state, not own state

---

## Debug Log

`debug_log.py` should provide a centralized debug-facing log interface.

Possible roles:
- tag-based debug messages
- overlay/console log feed integration
- optional file logging later
- log level control

Recommended rule:
- do not scatter random `print()` debugging forever
- funnel debug logs through one predictable path

---

## Console

The debug console may later support:
- command execution
- toggles
- runtime variable inspection
- debug actions
- invoking test/debug hooks

It is not required to be fully interactive in version one.

---

## Activation and Toggles

Debug tools should be controlled explicitly.

Potential controls:
- config flag enables debug mode
- input action toggles overlay
- separate action toggles inspector
- separate action toggles console

These should not be hidden behind random hardcoded keys.

---

## Production Safety

Recommended rule:
- debug tools may exist in shipped builds, but should be disabled unless explicitly enabled
- debug visuals should not interfere with gameplay/UI flow unless intentionally opened

---

## Data Ownership

Debug tools should observe existing systems.

They should not:
- become the source of truth for application state
- require systems to restructure themselves unnaturally
- store unrelated business logic

---

## Rules for Future Development

1. Keep debug tools optional.
2. Keep them layered on top of normal runtime behavior.
3. Keep logs centralized.
4. Prefer read-only inspection behavior where possible.
5. Do not let debug code leak heavily into clean runtime contracts.

---

## Open Questions

- Should the console support commands in version one?
- Should the inspector be text-based, visual, or both?
- Should debug overlays be composable modules?
- Should log history persist across scene changes?
