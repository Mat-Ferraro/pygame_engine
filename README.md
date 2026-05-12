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
- Persistence infrastructure (save/load plumbing)
- Audio manager
- Animation and particle helpers
- Debug overlay tools

It is not a genre-specific gameplay engine. Game-specific logic, domain models, and save schemas belong in the projects built on top of it.

## Project Structure

```
pygame_engine/          ← repo root
├── docs/               ← architecture and design documentation
├── examples/           ← runnable usage examples and smoke tests
├── tests/              ← automated tests
├── pygame_engine/      ← the importable package
│   ├── animation/
│   ├── app/
│   ├── assets/
│   ├── audio/
│   ├── debug/
│   ├── events/
│   ├── graphics/
│   ├── input/
│   ├── layout/
│   ├── particles/
│   ├── persistence/
│   ├── scene/
│   ├── state/
│   ├── theme/
│   ├── ui/
│   └── utils/
├── main.py             ← development entry point
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

## Usage

```python
from pygame_engine.app import Application, AppConfig
from pygame_engine.scene import Scene

class MyScene(Scene):
    ...

config = AppConfig(title="My Game", width=1280, height=720)
app = Application(config)
app.start(MyScene())
app.run()
```

See `docs/using_pygame_engine.md` for a full usage guide.
See `examples/` for runnable examples.

## Documentation

All architecture decisions and system contracts live in `docs/`.

Key documents:
- `docs/architecture.md` — overall system design
- `docs/accepted_decisions.md` — current accepted rules
- `docs/decision_log.md` — historical decision record
- Individual system docs for scene, UI, input, theme, etc.

## Requirements

- Python 3.11+
- pygame-ce (or pygame 2.x)
