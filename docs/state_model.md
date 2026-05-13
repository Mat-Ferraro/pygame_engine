# State Model

## Purpose

The state model defines what kinds of runtime state belong in the shared
engine infrastructure and how that state should be represented.

The engine supports some shared runtime state, but it should not become a
giant application-specific state container.

---

## Accepted Core Decisions

- Engine-level shared state should remain limited to engine/runtime concerns
- Game-specific domain state does not belong in the engine
- Observability should be used intentionally, not everywhere
- State ownership should remain explicit

---

## Current State Modules

The `state/` package contains:

- `observable.py` — reactive value wrapper with subscriber callbacks
- `runtime_flags.py` — named boolean engine flags with module-level singleton

`state_store.py` was considered and deliberately not implemented. See
Locked Implementation Decisions below.

---

## Design Principles

1. Keep engine state small and generic.
2. Separate engine-level state from game/project-level state.
3. Prefer explicit ownership.
4. Use observability where it helps, not everywhere by default.

---

## What Belongs in Engine State

Examples:
- debug flags
- runtime tool toggles
- window mode state

These are framework concerns, not game concerns.

---

## What Does Not Belong in Engine State

Examples:
- hero stats, inventory, quests, combat state
- save-game domain models
- game-specific configuration

Those belong in the consuming game project.

---

## Observable Values

`Observable[T]` wraps a single value and notifies subscribers on change.

```python
from pygame_engine.state.observable import Observable

hp = Observable(100)
hp.subscribe(lambda new, old: hud.update_hp(new))
hp.value = 75   # → hud.update_hp(75) fires automatically
```

Use observables when:
- Multiple consumers care about a changing value
- UI should react to a runtime change
- Loose coupling between producer and consumers is helpful

Do not use observables just because they exist.

---

## Runtime Flags

`RuntimeFlags` holds named boolean switches for engine behaviour.

```python
from pygame_engine.state.runtime_flags import flags

flags.debug        # True when debug mode is active
flags.show_fps     # True to show FPS in overlay
flags.show_rects   # True to draw widget bounding rects
flags.show_overlay # True to show the debug overlay
```

Flags are reset to False on each `Application.run()` call and then
set according to `AppConfig.debug`.

Game projects should subclass `RuntimeFlags` for their own flags rather
than adding to the engine class.

---

## State and Events

State and events are related but distinct:

- **State** (`Observable`, `RuntimeFlags`) — current truth, reactive
- **Events** (`EventBus`) — notifications that something happened

Do not use events as state. Do not replace meaningful notifications with
silent state writes when subscribers need change awareness.

See `docs/event_model.md` for the full event system documentation.

---

## Ownership Rules

Every piece of state should have an obvious owner:

- Scene-local values → the scene
- Widget-local state → the widget
- App-level runtime flags → `RuntimeFlags` / `Application`
- Engine-global state → rare and deliberate

---

## Mutation Rules

State mutation should be explicit, easy to trace, and consistent.

Avoid:
- Hidden mutation through deeply nested helpers
- Silent state change side effects
- Random writes into shared containers from unrelated systems

---

## Locked Implementation Decisions

### `state_store.py` was not implemented
**Decision:** No generic key-value state store exists in the engine.
`Observable` covers reactive value use cases. `RuntimeFlags` covers engine
boolean flags. A generic store has no concrete use case and creates
dumping-ground risk — anything that doesn't fit neatly elsewhere would
end up there.

### `Observable` uses callback-list notification, not the event bus
**Decision:** `Observable` maintains its own `_listeners` list and calls
them directly. It does not use `events/event_bus.py`.
**Reason:** Observable is a low-level primitive. Depending on the event
bus would create circular dependency risk and add indirection with no
benefit at this scale.

### `RuntimeFlags` uses named attributes, not a dict
**Decision:** Flags are named attributes (`flags.debug`, `flags.show_fps`)
not dict keys (`flags["debug"]`).
**Reason:** Named attributes give autocomplete, prevent typos, and make
the available flags self-documenting.

### Module-level `flags` singleton reset by Application on startup
**Decision:** A module-level `flags: RuntimeFlags` instance is provided.
`Application._startup()` calls `flags.reset()` then applies `config.debug`.
**Reason:** Any module can import `flags` and read the current state
without needing a reference to `Application`. Reset on startup ensures
a clean state every run.

### Game projects subclass RuntimeFlags for their own flags
**Decision:** Game-specific flags belong in a subclass of `RuntimeFlags`
in the game project, not as additions to the engine class.
**Reason:** Keeps the engine flags minimal and generic.
