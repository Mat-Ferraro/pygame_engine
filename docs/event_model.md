# Event Model

## Purpose

The event model defines how loosely-coupled subsystems communicate inside `pygame_engine`.

The goal is to support useful signaling without creating event spaghetti.

---

## Current Event Modules

The events package currently contains:

- `signals.py`
- `event_bus.py`

Suggested roles:
- `signals.py` = signal/event definitions or lightweight signal primitives
- `event_bus.py` = subscription and dispatch infrastructure

---

## Design Principles

1. Use direct calls when ownership is clear.
2. Use events when decoupling is genuinely useful.
3. Avoid replacing normal control flow with indiscriminate event broadcasting.
4. Define event lifetimes and subscription ownership clearly.

---

## When to Use Events

Good use cases:
- UI callbacks crossing subsystem boundaries
- debug notifications
- global runtime notifications
- theme/input/runtime changes that multiple systems may observe
- tool-style overlays reacting to engine state changes

Poor use cases:
- replacing ordinary method calls between tightly related objects
- hiding simple dependencies behind generic event names
- core scene/widget control flow where direct ownership is already obvious

---

## Event Bus Responsibilities

The event bus should:
- register subscribers
- unregister subscribers
- dispatch events/signals
- remain simple and predictable
- avoid magical global behavior where possible

It should not:
- become the universal backbone for every interaction
- silently swallow debugging needs around subscription lifetime
- hide ownership problems

---

## Signal Definitions

`signals.py` may define:
- named event types
- signal classes
- payload shape conventions
- reusable signal channels

Recommended rule:
- signal naming should be explicit and descriptive

Examples:
- `THEME_CHANGED`
- `SCENE_PUSHED`
- `DEBUG_OVERLAY_TOGGLED`

---

## Subscription Ownership

This is one of the most important rules.

Whoever subscribes is responsible for unsubscribing when its lifetime ends.

Examples:
- scenes unsubscribe on exit
- widgets unsubscribe on destruction/removal
- debug overlays unsubscribe when disabled or removed

Unclear subscription lifetime is one of the fastest ways to create bugs.

---

## Payload Policy

Events should carry enough information to be useful, but not arbitrary giant state blobs.

Good payloads:
- changed value
- source identifier
- scene reference if appropriate
- small contextual data

Avoid:
- entire app state dumps
- giant mutable objects unless truly necessary

---

## Local vs Global Events

### Local events
Used within a scene or widget hierarchy.
Often better handled via callbacks or direct ownership.

### Global/runtime events
Used for broader coordination across systems.
These are better candidates for the event bus.

Recommended rule:
- default to local/direct communication first
- escalate to bus-style communication only when appropriate

---

## Event Consumption

Events on the bus are different from input event consumption.

Input events may be consumed in routing.
Bus events are typically broadcasts to subscribers.

Do not mix these concepts.

---

## Rules for Future Development

1. Prefer direct calls when ownership is clear.
2. Use events for cross-cutting decoupling, not ordinary control flow.
3. Keep subscription lifetimes explicit.
4. Keep payloads small and clear.
5. Document new important engine-wide events.

---

## Open Questions

- Should signals be string constants, dataclasses, or lightweight classes?
- Should the event bus support priorities?
- Should there be scene-local event buses?
- Should event dispatch be synchronous only?
