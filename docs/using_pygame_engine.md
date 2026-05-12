# Using pygame_engine

## Purpose

This document explains how a future game project should use `pygame_engine`.

It is written from the perspective of a project built **with** the engine, not the engine itself.

---

## Accepted Direction

`pygame_engine` is a lightweight framework.

That means a future game project should rely on it for:
- runtime structure
- scenes
- UI primitives
- layout helpers
- input abstraction
- theming
- shared asset, persistence, audio, and debug support

It should **not** expect the engine to contain game-specific systems or genre rules.

---

## What Belongs in the Engine

`pygame_engine` should provide:
- application runtime shell
- scene system
- UI primitives
- layout helpers
- input abstraction
- theme system
- asset, persistence, audio, and debug helpers
- animation and particle support

---

## What Belongs in a Game Project

A game project should own:
- gameplay rules
- models/entities
- progression systems
- save payload schemas
- content data
- story/dialogue
- game-specific scenes
- game-specific composite widgets

Engine stays generic.
The game project contains the unique behavior.

---

## Typical New Game Structure

A future game project might look like:

```text
my_game/
  assets/
  data/
  game/
    scenes/
    systems/
    models/
    ui/
    persistence/
  main.py
```

The game imports `pygame_engine` for framework support.

---

## First Things a New Game Should Create

A new project using the engine will usually need:

1. an application entry point
2. an initial scene
3. game-specific scene classes
4. game-specific data/models/systems
5. optional composite widgets built from engine widgets

---

## Recommended Startup Flow

A new game should:
1. configure the application
2. create the initial scene
3. create the `Application`
4. hand the initial scene to scene management
5. run the app loop

Exact API may change, but the concept should stay stable.

---

## Scenes in a Game Project

Game scenes should use engine scene contracts.

Examples:
- main menu scene
- gameplay scene
- settings scene
- pause overlay

Accepted engine direction:
- scene flow is stack-based
- scenes may own a `root_widget`
- scenes should stay focused on coordination and flow

---

## Widgets in a Game Project

The engine should provide reusable primitive widgets like:
- `Button`
- `Panel`
- `Label`
- `TextBlock`
- `Dropdown`
- `Tooltip`
- `Toast`

A game project may build composite widgets from these:
- `PartyPanel`
- `InventoryCard`
- `MissionSummaryPanel`

Those composites usually belong in the game repo, not the engine.

---

## Public Imports

Preferred usage direction:

```python
from pygame_engine.ui import Button
from pygame_engine.scene import Scene
```

Game projects should not need to rely on deep internal import paths for common engine features.

---

## Theme Usage

A game should normally:
- start from engine defaults
- override colors, fonts, spacing, or styles as needed
- avoid modifying engine widget logic just to change visuals

The theme system exists to separate style from behavior.

---

## Input Usage

A game should:
- use action-based input where possible
- define project-specific bindings if needed
- avoid scattering raw key handling everywhere

This keeps controls easier to change later.

---

## Asset Usage

A game should:
- keep game assets in its own asset structure
- use engine asset helpers for loading/caching
- avoid one-off loading code in every scene

The engine currently prefers lazy loading with caching and loud failure during development.

---

## Persistence Usage

A game should use engine persistence for infrastructure, not game meaning.

### Use the engine for:
- save slot handling
- safe read/write helpers
- metadata/version support
- migration infrastructure
- generic serializer support

### Use the game project for:
- defining what gets saved
- building the save payload
- reconstructing game state from saved data
- game-specific migration rules

### Recommended pattern
1. game project builds plain serializable save payload
2. engine persistence layer writes and reads that payload safely
3. game project reconstructs domain objects from loaded payload

This keeps the engine generic and the game-specific save model where it belongs.

---

## Debug Tool Usage

Debug tools are intended to be supported and useful during game development.

A game project should:
- use engine debug overlays and tools where they help
- avoid baking project-specific debug hacks into the engine
- wire project-level debug needs cleanly on top of engine support

---

## Documentation Discipline

When building with the engine:
- update engine docs when engine contracts change
- update game docs when game architecture decisions are made
- avoid relying only on chat history or memory for major decisions

---

## Recommended Workflow

1. use engine primitives first
2. extend only when a real gap exists
3. keep game-specific logic out of engine packages
4. document framework-level decisions as they happen
5. add examples/tests when reusable behavior is introduced

---

## Rules for Future Projects

1. The engine should remain generic.
2. Game projects should compose engine primitives into project-specific behavior.
3. If the same project-specific pattern appears across multiple projects, only then consider moving it into the engine.
4. Avoid promoting one project’s temporary needs into engine architecture too early.
