# Naming Conventions

## Goal

These naming rules keep `pygame_engine` consistent, readable, and scalable.

---

## General Rules

- Use **lowercase snake_case** for packages, modules, and functions.
- Use **PascalCase** for classes.
- Use **UPPER_SNAKE_CASE** for module-level constants.
- Prefer short, explicit nouns for module names.
- Avoid vague names like `helpers`, `misc`, `common`, or `stuff`.

---

## Folder Names

Folders should usually be:
- lowercase
- noun-based
- broad enough to group related concepts
- narrow enough to have a clear responsibility

Examples:
- `scene`
- `layout`
- `theme`
- `graphics`
- `particles`

Avoid:
- `core`
- `shared_stuff`
- `helpers`
- `misc`

---

## Module Names

### Preferred patterns
Use singular names when a module centers on one primary concept:
- `button.py`
- `panel.py`
- `scene.py`
- `particle.py`
- `observable.py`

Use plural names when a module contains sets, registries, presets, or grouped constants:
- `tokens.py`
- `signals.py`
- `presets.py`
- `bindings.py`
- `actions.py`

### Responsibility-first naming
Choose names that describe what the file is for:
- `asset_loader.py`
- `sprite_loader.py`
- `sprite_renderer.py`
- `scene_manager.py`
- `state_store.py`

Avoid ambiguous names when a clearer one exists:
- prefer `draw_utils.py` over `draw.py` if it holds helper functions
- prefer `debug_log.py` over `logging.py` to avoid standard-library confusion

---

## Class Names

Classes should be:
- PascalCase
- singular
- concept-oriented

Examples:
- `Application`
- `Scene`
- `SceneManager`
- `SceneStack`
- `Widget`
- `Button`
- `Panel`
- `ThemeRuntime`

Avoid:
- `Buttons`
- `UtilsManager`
- `BaseThingHandler`

---

## Function Names

Functions should be:
- snake_case
- action-oriented
- explicit about what they do

Examples:
- `load_image`
- `draw_panel`
- `push_scene`
- `set_theme`
- `bind_action`

Avoid:
- `do_it`
- `handle`
- `process_stuff`

---

## Constant Names

Use `UPPER_SNAKE_CASE` for:
- fixed configuration defaults
- event names if they are constants
- hardcoded token identifiers
- module-level sentinels

Examples:
- `DEFAULT_WINDOW_WIDTH`
- `MAX_PARTICLE_COUNT`
- `DEFAULT_THEME_NAME`

---

## File Role Guidelines

### Assets vs graphics
- `assets/*` loads or caches files
- `graphics/*` draws, transforms, or renders things

### UI modules
- `ui/base/*` = foundational contracts
- `ui/containers/*` = composition and grouping widgets
- `ui/controls/*` = interactive controls
- `ui/feedback/*` = temporary or reactive feedback widgets
- `ui/text/*` = text presentation widgets

### Scene modules
- `scene.py` = scene contract
- `scene_manager.py` = orchestration
- `scene_stack.py` = layered scene behavior
- `transitions.py` = visual transition logic

---

## Public API Naming

Exports exposed to users of the framework should feel stable and clean.

Prefer:
```python
from pygame_engine.ui import Button
from pygame_engine.scene import Scene
from pygame_engine.theme import ThemeRuntime
```

Avoid forcing consumers to import deep internal paths unless necessary.

---

## Private/Internal Naming

For internal-only helpers, use a leading underscore where helpful:
- `_resolve_padding`
- `_clamp_alpha`
- `_dispatch_event`

Use this sparingly. Not every helper must be private, but internal implementation details should be easy to recognize.

---

## Naming Decision Log

### Accepted
- lowercase snake_case packages and modules
- PascalCase classes
- category-based UI package layout
- explicit distinction between load vs render responsibilities

### Avoid
- vague bucket names like `misc`, `common`, `helpers`
- duplicate file names with different meanings in different packages unless the distinction is extremely obvious
