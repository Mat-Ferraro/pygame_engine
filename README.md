# pygame_engine

A lightweight, reusable framework built on top of pygame.

## Purpose

`pygame_engine` provides a clean foundation for pygame projects:
- Application loop and lifecycle management
- Stack-based scene flow
- Reusable UI primitives and layout helpers
- Theme system with design tokens and runtime overrides
- Action-based input abstraction
- Asset loading with lazy caching
- Persistence infrastructure
- Audio manager
- Animation and particle helpers
- Debug overlay tools

It is not a genre-specific gameplay engine.

## Current State

`pygame_engine` is in active early development.

### Implemented now
- `Application`, `AppConfig`
- `Scene`, `SceneManager`, `SceneStack`
- `InputManager`, action constants, default bindings
- Layout helpers: `anchor`, `row`, `column`, `grid`
- Theme runtime/default theme
- `Widget`, `Panel`, `Stack`, `Button`, `Label`, `TextBlock`
- Runnable examples and a growing automated test suite

### Planned / stubbed
- `Dropdown`
- Debug tools
- Asset pipeline implementation
- Persistence implementation
- Audio implementation
- Animation/particle implementation

## Usage

```python
from pygame_engine.app import Application, AppConfig
from pygame_engine.scene import Scene

class MyScene(Scene):
    pass

config = AppConfig(title="My Game", width=1280, height=720)
app = Application(config)
app.run(MyScene())
```

See `docs/using_pygame_engine.md` for the broader usage guide.
