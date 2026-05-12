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

## Repository Layout Names

The repo root contains four top-level areas. Their names are fixed:

| Path              | Role                                                    |
|-------------------|---------------------------------------------------------|
| `pygame_engine/`  | The importable Python package                           |
| `docs/`           | Architecture decisions and system documentation         |
| `examples/`       | Runnable usage examples and manual smoke tests          |
| `tests/`          | Automated test suite                                    |

`docs/`, `examples/`, and `tests/` are **not** inside the importable package.
They live at the repo root so the installed package stays clean.

---

## Package / Folder Names

Folders inside `pygame_engine/` should be:
- lowercase
- noun-based
- broad enough to group related concepts
- narrow enough to have a clear responsibility

Current packages: `animation`, `app`, `assets`, `audio`, `debug`, `events`,
`graphics`, `input`, `layout`, `particles`, `persistence`, `scene`, `state`,
`theme`, `ui`, `utils`.

Avoid: `core`, `shared_stuff`, `helpers`, `misc`.

---

## Module Names

### Singular — module centres on one primary concept
- `button.py`, `panel.py`, `scene.py`, `particle.py`, `observable.py`

### Plural — module contains sets, registries, presets, or grouped constants
- `tokens.py`, `signals.py`, `presets.py`, `bindings.py`, `actions.py`

### Responsibility-first naming
- `asset_loader.py`, `sprite_loader.py`, `sprite_renderer.py`
- `scene_manager.py`, `state_store.py`

Avoid ambiguous names when a clearer one exists:
- prefer `draw_utils.py` over `draw.py`
- prefer `debug_log.py` over `logging.py` (avoids stdlib confusion)

---

## Class Names

PascalCase, singular, concept-oriented.

Examples: `Application`, `Scene`, `SceneManager`, `SceneStack`, `Widget`,
`Button`, `Panel`, `ThemeRuntime`.

Avoid: `Buttons`, `UtilsManager`, `BaseThingHandler`.

---

## Function Names

snake_case, action-oriented, explicit about what they do.

Examples: `load_image`, `draw_panel`, `push_scene`, `set_theme`, `bind_action`.

Avoid: `do_it`, `handle`, `process_stuff`.

---

## Constant Names

`UPPER_SNAKE_CASE` for:
- fixed configuration defaults
- event names when constants
- hardcoded token identifiers
- module-level sentinels

Examples: `DEFAULT_WINDOW_WIDTH`, `MAX_PARTICLE_COUNT`, `DEFAULT_THEME_NAME`.

---

## File Role Guidelines

### Assets vs graphics
- `assets/*` loads or caches files from disk
- `graphics/*` draws, transforms, or renders things

### UI modules
- `ui/base/*` = foundational widget contracts
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

Exports exposed to consumers of the framework should feel stable and clean.

Prefer:
```python
from pygame_engine.ui import Button
from pygame_engine.scene import Scene
from pygame_engine.theme import ThemeRuntime
```

Avoid forcing consumers to import deep internal paths for common features.

---

## Private / Internal Naming

Use a leading underscore for internal-only helpers:
- `_resolve_padding`, `_clamp_alpha`, `_dispatch_event`

Use sparingly. Not every helper must be private, but internal implementation
details should be easy to recognise.

---

## Test File Naming

Test files live in `tests/` at the repo root.

Naming rule: `test_<module>.py`

Examples: `test_easing.py`, `test_layout.py`, `test_rects.py`, `test_timers.py`.

A shared `tests/conftest.py` provides the headless pygame fixture used by all tests.

---

## Example File Naming

Example files live in `examples/` at the repo root.

Naming rule: `example_<topic>.py`

Examples: `example_app.py`, `example_scene.py`, `example_buttons.py`.

---

## Accepted Decisions

- lowercase snake_case packages and modules
- PascalCase classes
- category-based UI package layout
- explicit distinction between load vs render responsibilities
- `docs/`, `examples/`, `tests/` at repo root, not inside the package

## Avoid

- vague bucket names: `misc`, `common`, `helpers`
- duplicate file names with different meanings in different packages unless
  the distinction is extremely obvious
- placing developer tooling (docs, tests, examples) inside the importable
  package tree
