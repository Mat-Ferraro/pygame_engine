# Application Contract

## Purpose

The `Application` is the top-level runtime owner for a project built on `pygame_engine`.

It is responsible for bootstrapping pygame, owning the main loop, coordinating the high-level runtime, and exposing shared services to the rest of the framework.

The `Application` should be one of the most stable contracts in the entire engine.

---

## Accepted Core Decisions

The application layer currently assumes:

- `pygame_engine` is a lightweight framework, not a genre engine
- the scene runtime model is stack-based
- debug tools are important and should be supported, but as optional layers
- engine-level shared state should stay limited to engine/runtime concerns
- typing should be moderate but intentional

---

## Responsibilities

`Application` is responsible for:

- initializing and shutting down pygame
- creating and owning the display surface/window
- owning the master clock / delta-time source
- driving the frame loop
- routing events into the active scene flow
- updating and rendering the current scene stack
- initializing shared runtime services
- applying high-level configuration
- integrating optional debug systems
- managing application shutdown state

It should act as the runtime shell of the engine.

---

## Non-Responsibilities

`Application` should **not**:

- contain gameplay logic
- contain scene-specific logic
- contain widget-specific logic
- act as a general-purpose global store
- become a giant service locator without discipline
- directly handle project-specific menus, game rules, or domain models

---

## Core Ownership

The `Application` should own or coordinate:

- pygame initialization state
- display/window
- master surface references
- clock / frame timing
- `SceneManager`
- optional `InputManager`
- optional `ThemeRuntime`
- optional asset/audio/debug services
- run-state flags such as `is_running`

---

## Suggested Lifecycle

### Construction
The object is created with configuration and optional service dependencies.

Typical responsibilities:
- store config
- prepare service references
- validate required runtime settings

### Startup
A dedicated startup method should:
- initialize pygame
- create the window
- create the clock
- initialize runtime services
- create or attach the initial scene
- mark the application as running

### Main Loop
The main loop should repeatedly:
1. gather events
2. update input state
3. route events
4. update runtime systems
5. render current scene(s)
6. present the frame
7. compute the next frame delta time

### Shutdown
Shutdown should:
- cleanly stop the run loop
- release resources where needed
- call pygame quit behavior
- avoid partial shutdown states

---

## Main Loop Contract

The main loop should be predictable and easy to reason about.

Recommended order:

```text
poll events
update input snapshot
route events to scene flow
update scene flow
update debug/runtime overlays
clear backbuffer
render scene flow
render overlays/debug
flip/present display
tick clock / compute dt
```

This order can be adjusted slightly, but it should remain stable once chosen.

---

## Event Routing

The `Application` should gather raw pygame events and route them consistently.

Recommended routing philosophy:
1. application-level essential handling
2. topmost/modal scene or overlay
3. focused widget / UI layer
4. scene-level logic
5. global debug/runtime shortcuts

This reflects accepted input-routing decisions.

---

## Window and Display Ownership

The `Application` should define:
- initial window size
- fullscreen/windowed behavior
- resizable behavior
- caption/title behavior
- display flags
- resize update handling

Recommended rule:
- scene and widget code should not directly recreate the window
- display creation remains application-owned

---

## Delta Time

The `Application` is the trusted source of frame delta time.

Rules:
- `dt` should be produced once per frame
- `dt` should be passed into updates, not recomputed in many places
- optional dt clamping may be applied to prevent huge spikes after stalls

---

## Shared Services

The `Application` may expose shared engine services, but this should remain disciplined.

Potential services:
- input
- theme
- assets
- audio
- debug tools
- event bus
- runtime flags

Recommended rule:
- only expose truly cross-cutting services
- avoid turning `Application` into a bag of globals

---

## Scene Integration

The `Application` owns the active scene flow indirectly through `SceneManager`.

It should:
- set the initial scene
- invoke manager update/render/event methods
- remain agnostic to scene-specific behavior

It should not:
- directly manipulate scene internals
- special-case individual scenes

---

## Debug Integration

Debug tools are important, but should remain optional runtime layers.

The `Application` is the correct place to integrate:
- fps counters
- debug overlays
- dev console toggles
- frame timing displays
- inspector activation

Recommended rule:
- debug systems are supported but not required for basic engine function

---

## Configuration

`app/config.py` should define engine/application configuration defaults.

Typical config areas:
- window title
- width/height
- vsync
- target FPS
- resizable
- debug enabled
- default theme name
- asset root

Recommended rule:
- `Application` consumes config, but config should not own logic

---

## Suggested Public Interface

Possible methods and properties:

- `start()`
- `run()`
- `stop()`
- `shutdown()`
- `handle_event(event)`
- `update(dt)`
- `render(surface)`

Possible properties:
- `is_running`
- `config`
- `display_surface`
- `clock`
- `scene_manager`
- `input_manager`

This is a suggested direction, not a locked API.

---

## Rules for Future Development

1. Keep `Application` small and predictable.
2. Do not let it absorb gameplay code.
3. Do not let it become a universal dependency container.
4. Keep frame order stable once decided.
5. Treat it as core framework infrastructure, not an extension playground.

---

## Open Questions

- Should `Application` own `InputManager`, or should input be externally attached?
- Should rendering always target the main display surface, or support an off-screen render target?
- Should there be a distinct bootstrap stage before full startup?
- How much service access should scenes receive directly?
