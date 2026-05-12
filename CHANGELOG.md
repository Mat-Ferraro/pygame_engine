# Changelog

All notable changes to `pygame_engine` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Fixed
- `tests/test_button.py` — added missing `import pygame` and `from pygame_engine.ui.controls import Button`
- `tests/test_scene_manager.py` — added missing `from pygame_engine.scene import Scene, SceneManager`
- `pygame_engine/ui/base/widget.py` — removed stale docstring note saying theme access was deferred; theme is live via `get_theme()`
- `examples/example_buttons.py` — replaced transparent root `Panel` with `Stack` (the correct container for this use case)
- `docs/docs_roadmap.md` — removed (was a duplicate of `docs/roadmap.md`; `roadmap.md` is the canonical file)

### Added — Tests
- `tests/test_timers.py` — full coverage of `Timer` and `Cooldown`: start/stop/reset, progress, elapsed/remaining, Cooldown.fired and carry-over
- `tests/test_layout.py` — full coverage of `anchor`, `row`, `column`, `grid`: positions, sizes, spacing, padding, alignment, edge cases
- `tests/test_rects.py` — full coverage of rect helpers: construction, inset, snap, clamp_inside, split_horizontal/vertical
- `tests/test_button.py` — added `test_no_click_without_prior_press_inside`
- `tests/test_scene_manager.py` — added `test_pop_empty_stack_returns_none`, `test_is_empty_reflects_stack_state`

---

## Previous work (summary)

### Infrastructure
- Established repo structure: `docs/`, `examples/`, `tests/` at root; `pygame_engine/` as the importable package
- `pyproject.toml`, `.gitignore`, `README.md`, `CHANGELOG.md`
- `tests/conftest.py` — headless pygame session fixture

### Runtime spine
- `pygame_engine/app/` — `Application`, `AppConfig`
- `pygame_engine/scene/` — `Scene`, `SceneManager`, `SceneStack`, `transitions.py` (stub)
- `pygame_engine/ui/base/` — `Widget`

### Input
- `pygame_engine/input/` — `InputManager`, `actions`, `DEFAULT_BINDINGS`

### Layout
- `pygame_engine/layout/` — `anchor`, `row`, `column`, `grid`, `_shared`

### Theme
- `pygame_engine/theme/` — `tokens`, `defaults` (full dataclass hierarchy), `runtime` (`get_theme` / `set_theme` / `reset_theme`)

### UI widgets
- `pygame_engine/ui/text/` — `Label`, `TextBlock`
- `pygame_engine/ui/controls/` — `Button`
- `pygame_engine/ui/containers/` — `Panel`, `Stack`

### Utils
- `pygame_engine/utils/` — `Timer`, `Cooldown`, `colors`, `rects`, `mathx`

### Examples
- `examples/example_app.py` — spine smoke test
- `examples/example_buttons.py` — Panel, Button, Label, layout
- `examples/example_scene.py` — scene push/pop/replace/overlay
- `examples/example_layout.py` — all four layout helpers

### Tests
- `tests/test_widget.py`, `test_button.py`, `test_scene_stack.py`, `test_scene_manager.py`, `test_timers.py`, `test_layout.py`, `test_rects.py`
