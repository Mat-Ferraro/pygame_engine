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

---

## Locked Implementation Decisions

### All four debug modules implemented; console is display-only in v1
**Decision:** `debug_log`, `overlay`, `inspector`, `console` are all
implemented. The console is display-only — no command input in v1.
**Reason:** Interactive console requires text input mode which isn't built
yet. A read-only log tail covers the real v1 need.

### Overlay and console share the `show_overlay` flag
**Decision:** Both render when `flags.show_overlay` is True. F1 toggles
this flag. A separate console toggle can be split out later if needed.
**Reason:** Simplest model that covers the real use case.

### Overlay renders in `Application._loop` after scenes, before flip
**Decision:** `DebugOverlay.render()` and `DebugConsole.render()` are
called by `Application` after scene rendering. They are not scene widgets.
**Reason:** Debug tools must always appear on top of everything. Putting
them in `Application._loop` rather than the scene tree guarantees this.

### Inspector writes to debug_log, not stdout
**Decision:** `Inspector.dump()` calls `log()` — output appears in the
debug console and log history, not printed to stdout.
**Reason:** Keeps debug output in one place and makes it accessible from
the on-screen console.

### Debug tools check their own flags — callers don't need to
**Decision:** `DebugOverlay.render()` and `DebugConsole.render()` check
`flags.show_overlay` internally and return immediately if False.
**Reason:** Callers (Application) can always call render() unconditionally.
No `if flags.debug:` guards needed at the call site.
