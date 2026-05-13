## Purpose

The state model defines what kinds of runtime state belong in the shared engine infrastructure and how that state should be represented.

The engine should support some shared runtime state, but it should not become a giant application-specific state container.

---

## Accepted Core Decisions

The state model currently assumes:

- engine-level shared state should remain limited to engine/runtime concerns
- game-specific domain state does not belong in the engine
- observability should be used intentionally, not everywhere
- state ownership should remain explicit

---

## Current State Modules

The state package currently contains:

- `observable.py`
- `runtime_flags.py`
- `state_store.py`

Suggested roles:
- `observable.py` = reactive-ish value wrapper or subscription-aware state primitive
- `runtime_flags.py` = boolean/toggle-style runtime flags
- `state_store.py` = structured shared runtime state container

---

## Design Principles

1. Keep engine state small and generic.
2. Separate engine-level state from game/project-level state.
3. Prefer explicit ownership.
4. Use observability where it helps, not everywhere by default.

---

## What Belongs in Engine State

Examples:
- active theme name
- debug flags
- UI focus state if centralized later
- window mode state
- runtime tool toggles
- engine service references if intentionally managed

These are framework concerns, not game concerns.

---

## What Does Not Belong in Engine State

Examples:
- hero stats
- inventory
- quests
- mission state
- combat state
- savegame domain models

Those belong in the consuming game project.

---

## Observable Values

`observable.py` may support:
- value change subscription
- explicit set/get
- change notifications
- optional previous-value tracking

Use observables when:
- multiple consumers care about a small changing value
- UI should react to a runtime change
- loose coupling is helpful

Do not use observables just because they exist.

---

## Runtime Flags

`runtime_flags.py` should hold boolean-like runtime switches.

Examples:
- debug overlay enabled
- inspector visible
- console open
- input capture mode enabled

Recommended rule:
- flags should be limited, named clearly, and not become a substitute for proper state structure

---

## State Store

`state_store.py` may provide a structured shared runtime store.

Possible uses:
- engine-level state registry
- keyed runtime state values
- optional shared access surface for small framework-level data

Recommended rule:
- keep it narrow
- avoid turning it into a universal dumping ground

---

## Ownership Rules

Every piece of state should have an obvious owner.

Examples:
- scene-local values belong to scenes
- widget-local state belongs to widgets
- app-level runtime flags belong to application/runtime infrastructure
- engine-global state should be rare and deliberate

---

## Mutation Rules

State mutation should be:
- explicit
- easy to trace
- consistent

Avoid:
- hidden mutation through deeply nested helpers
- silent state change side effects
- random writes into global stores from unrelated systems

---

## State and Events

State and events are related but distinct.

- state = current truth
- events = notifications about change or occurrences

Do not use events as state.
Do not use state writes as a substitute for meaningful notifications when subscribers need change awareness.

---

## Rules for Future Development

1. Keep engine state generic and small.
2. Keep ownership explicit.
3. Use observables where they add real value.
4. Avoid giant all-purpose stores.
5. Keep game-specific state out of the engine.

---

## Open Questions

- Should `StateStore` be dictionary-like, typed, or both?
- Should observables be standalone values or store-backed?
- Should state changes emit events automatically?
- How much state should the app expose to scenes directly?

---

## Locked Implementation Decisions

### `state_store.py` is not implemented
**Decision:** `state_store.py` remains an empty stub. No generic key-value
state store is implemented.
**Reason:** The doc's own warning still holds — a generic store is a
dumping ground waiting to happen. Both `Observable` and `RuntimeFlags`
cover the real engine-level state needs without a general store.

### `Observable` uses callback-list notification, not the event bus
**Decision:** `Observable` maintains its own `_listeners` list and calls
them directly. It does not use `events/event_bus.py`.
**Reason:** Observable is a low-level primitive. Making it depend on the
event bus would create a circular dependency risk and add indirection with
no benefit at this scale.

### `RuntimeFlags` is a typed class with named attributes, not a dict
**Decision:** Flags are named attributes (`flags.debug`, `flags.show_fps`)
not dict keys (`flags["debug"]`).
**Reason:** Named attributes give autocomplete, prevent typos, and make the
available flags self-documenting. A dict would be opaque.

### Module-level `flags` singleton, reset by Application on startup
**Decision:** A module-level `flags: RuntimeFlags` instance is provided.
`Application._startup()` calls `flags.reset()` then applies `config.debug`.
**Reason:** Allows any module to import `flags` and read the current state
without needing a reference to `Application`. Reset on startup ensures a
clean state every run.

### Game projects subclass RuntimeFlags for their own flags
**Decision:** Game-specific flags belong in a subclass of `RuntimeFlags`
in the game project, not as additions to the engine class.
**Reason:** Keeps the engine flags minimal and generic.
