## Purpose

This roadmap defines the planned development path for `pygame_engine`.

It exists to keep development intentional and prevent random feature drift.

---

## Accepted V1 Boundary

Version one currently aims to provide:
- `Application`
- `Scene`
- `SceneManager`
- `SceneStack`
- `Widget`
- `Panel`
- `Button`
- `Label`
- `TextBlock`
- `Stack`
- basic row/column layout
- theme runtime/defaults
- input manager/actions/bindings
- basic asset loading
- examples

This is the current accepted boundary.

---

## Phase 1 - Runtime Foundations

Primary goals:
- define `Application`
- define `Scene`
- define `SceneManager`
- define `SceneStack`
- define `Widget`

Deliverables:
- stable core contracts
- main loop behavior
- event/update/render order
- scene switching and stack support
- baseline widget lifecycle
- boolean event-consumption contracts

Status:
- implemented first-pass runtime spine
- hardened with targeted tests

---

## Phase 2 - Layout, Theme, Input

Primary goals:
- implement basic layout helpers
- implement theme token/default/runtime flow
- implement input action/binding/state flow

Deliverables:
- row/column/grid/anchor first-pass behavior
- theme-aware widget styling
- action-based input queries
- basic focus and input routing direction

Status:
- implemented first pass
- examples continue to grow

---

## Phase 3 - Core UI Toolkit

Primary goals:
- build foundational reusable widgets

Deliverables:
- panel
- stack container
- button
- dropdown
- label
- text block
- tooltip
- toast

Status:
- `Panel`, `Button`, `Label`, `TextBlock`, and `Stack` implemented
- `Dropdown`, `Tooltip`, and `Toast` still pending

Current recommendation:
- continue here next with `Dropdown`, then feedback widgets

---

## Phase 4 - Graphics, Animation, Particles

Primary goals:
- support visual polish systems

Deliverables:
- tween/easing integration
- animator runtime behavior
- draw utilities
- surface helpers
- sprite rendering helpers
- particle emitter and presets

---

## Phase 5 - Assets, Audio, Debug Tools

Primary goals:
- strengthen supporting systems

Deliverables:
- asset loading and caching flow
- font/sound/sprite loading helpers
- audio manager behavior
- debug overlay
- debug log integration
- inspector/console foundations

---

## Phase 6 - Public API and Usability Cleanup

Primary goals:
- improve developer experience for engine users

Deliverables:
- clean package exports
- improved examples
- stronger README usage guidance
- consistent docs updates
- test growth where needed

---

## Phase 7 - Stability and Expansion

Primary goals:
- refine based on actual usage

Potential directions:
- richer widget set
- advanced layout behavior
- input rebinding
- theme overrides
- scene transitions library
- more robust debug tooling
- packaging/release workflow

---

## Ongoing Rules

Throughout all phases:
- keep framework code generic
- keep docs updated with decisions
- add tests for reusable deterministic logic
- prefer small, stable contracts over rapid abstraction growth

---

## Current Priority

The current highest-priority work is:
1. implement `Dropdown`
2. implement `Tooltip` and `Toast`
3. add tests for `TextBlock` and `Stack`
4. expand examples before moving into secondary systems
