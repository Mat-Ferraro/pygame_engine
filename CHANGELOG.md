# Changelog

All notable changes to `pygame_engine` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Infrastructure
- Established project structure: repo root contains `docs/`, `examples/`, `tests/`, and the `pygame_engine/` package
- Moved `docs/`, `examples/`, and `tests/` out of the importable package tree to repo root
- Added `CHANGELOG.md`
- Added `tests/conftest.py` with headless pygame fixture
- All source modules are stubs pending implementation

---

_Development is currently in the architecture and infrastructure phase._

### Added — Application spine
- `pygame_engine/app/config.py` — `AppConfig` dataclass (window, timing, display, paths, debug)
- `pygame_engine/app/application.py` — `Application` class with full contract-level signatures:
  - Side-effect-free `__init__`
  - Single `run(initial_scene)` entry point
  - `_startup` / `_loop` / `_shutdown` lifecycle
  - Fixed frame-loop order (poll → input → events → update → render → flip → dt)
  - `_handle_event` with priority routing stubs
  - `_compute_dt` with configurable clamping
  - `stop()`, `config`, `is_running`, `display_surface`, `clock` properties
- `pygame_engine/app/__init__.py` — exports `Application`, `AppConfig`
- Locked four Application open questions; recorded in `decision_log.md` and `application_contract.md`

### Added — Scene system
- `pygame_engine/scene/scene.py` — `Scene` base class with full lifecycle hooks and frame methods
- `pygame_engine/scene/scene_stack.py` — `SceneStack` with blocking-policy traversals (input/update/render)
- `pygame_engine/scene/scene_manager.py` — `SceneManager` with push/pop/replace/clear_and_push and lifecycle hook orchestration
- `pygame_engine/scene/transitions.py` — documented stub (deferred)
- `pygame_engine/scene/__init__.py` — exports `Scene`, `SceneManager`, `SceneStack`
- `pygame_engine/app/application.py` — wired `SceneManager`; `run()` now accepts `Scene`; shutdown pops all scenes cleanly; `scene_manager` property added

### Added — Widget base
- `pygame_engine/ui/base/widget.py` — `Widget` base class with rect, interaction state (visible, enabled, hovered, focused), frame methods, `set_rect`, `contains_point`, `is_interactive` property
- `pygame_engine/ui/base/__init__.py` — exports `Widget`
- `pygame_engine/ui/__init__.py` — clean public import surface; other widgets stubbed/commented until implemented
- `pygame_engine/scene/scene.py` — `root_widget` now typed as `Widget | None`; all three frame method TODOs resolved with real delegation calls
- Locked Widget open questions; recorded in `widget_contract.md` and `decision_log.md`

### Added — Spine example
- `examples/example_app.py` — minimal end-to-end example exercising the full chain: AppConfig → Application → SceneManager → ExampleScene → ColourBlock (Widget subclass)
- `main.py` — uncommented to run example_app by default

### Added — Input system
- `pygame_engine/input/actions.py` — canonical action string constants (NAV_UP/DOWN/LEFT/RIGHT, CONFIRM, CANCEL, PAUSE, DEBUG_TOGGLE, INSPECTOR_TOGGLE, CONSOLE_TOGGLE)
- `pygame_engine/input/bindings.py` — default key-to-action mapping (DEFAULT_BINDINGS)
- `pygame_engine/input/input_manager.py` — per-frame input state: keyboard (pressed/released/down), mouse (pos, delta, buttons, wheel), action queries, rebinding support
- `pygame_engine/input/__init__.py` — exports InputManager and actions module
- `pygame_engine/app/application.py` — InputManager wired in; `update(events)` called each frame; `input_manager` property added
- `examples/example_app.py` — ESC quit now uses `was_action_pressed(actions.CANCEL)` instead of raw key check

### Added — Layout helpers
- `pygame_engine/layout/_shared.py` — internal `Align` type and `_resolve_align()` helper
- `pygame_engine/layout/anchor.py` — `anchor()`: place a rect at a named point within bounds (9 anchor points, margin, offset)
- `pygame_engine/layout/row.py` — `row()`: distribute items horizontally with spacing, padding, vertical align
- `pygame_engine/layout/column.py` — `column()`: distribute items vertically with spacing, padding, horizontal align
- `pygame_engine/layout/grid.py` — `grid()`: uniform grid with spacing and padding, centred block
- `pygame_engine/layout/__init__.py` — exports `anchor`, `column`, `grid`, `row`
- `examples/example_app.py` — replaced manual rect math with `anchor(screen, (200, 120), "center")`

### Added — Button and Label widgets
- `pygame_engine/ui/text/label.py` — `Label`: single-line text widget, cached render surface, left/center/right alignment, dirty-flag invalidation on text/colour/rect change
- `pygame_engine/ui/text/__init__.py` — exports `Label`
- `pygame_engine/ui/controls/button.py` — `Button`: clickable widget with `on_click` callback, normal/hovered/pressed/disabled visual states, internal `Label` for text
- `pygame_engine/ui/controls/__init__.py` — exports `Button`
- `pygame_engine/ui/__init__.py` — now exports `Widget`, `Button`, `Label`
- `examples/example_buttons.py` — demonstrates Button, Label, column layout, disabled state, status updates, ESC via action system
- `main.py` — updated to run example_buttons by default
