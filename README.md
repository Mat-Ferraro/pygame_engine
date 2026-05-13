Version 1.3.0

A lightweight, reusable framework built on top of pygame-ce for 2D games.

`pygame_engine` gives you a clean, structured foundation so you can focus
on making your game instead of rebuilding the same infrastructure every time.

---

## What it provides

**Core runtime**
- Application runtime — main loop, delta-time, window management, resize
- Stack-based scene system — push/pop/replace scenes with full lifecycle hooks
- Scene transitions — Fade, Slide (4 directions), Crossfade

**UI**
- 15 widgets — Button, Label, TextBlock, RichLabel, Panel, Stack, Scrollable,
  Checkbox, Slider, RadioGroup, Dropdown, InputField, ProgressBar, Toast, Tooltip
- Layout helpers — `row`, `column`, `grid`, `anchor` (stateless)
- Responsive layout — `FlexRow`, `FlexColumn`, `AnchorLayout` (resize-aware)
- Focus management — Tab/Shift+Tab traversal across focusable widgets

**Theme & styling**
- Design token system with a full default theme
- File-driven theming — `theme_from_file(path)` loads a JSON override, `reload_theme_file()` for live hot-reload
- File-driven theming — load a JSON file to override colours, sizes, spacing
- Live hot-reload — edit `assets/theme.json`, press R to see changes instantly
- Rich text — `[b]bold[/b]` `[i]italic[/i]` `[color=#rrggbb]coloured[/color]`

**Input**
- Action-based input — `was_action_pressed(CONFIRM)` not `is_key_down(K_RETURN)`
- Key remapping — change bindings at runtime, persist with `bindings_to_dict()`
- Controller support — hot-plug, axis→action mapping, dead zones, haptic feedback

**Game systems**
- Camera — follow, zoom, shake, world bounds, visibility culling
- Tilemap — multi-layer, collision, camera culling
- Dialogue — script format, state machine runner, typewriter box
- A* Pathfinding — grid-based, 4/8-directional, Tilemap integration
- 2D Lighting — dark overlay with radial gradient light sources, flicker
- Animation state machine — condition-driven transitions between animations
- 2D Positional audio — distance falloff, stereo panning

**Assets & data**
- Asset loading — lazy-cached images, fonts, sounds
- Sprite atlas — pack surfaces at startup, blit by name
- Localisation — key lookup, plural forms, runtime language switching
- Persistence — `SaveManager` with atomic writes and migration pipeline
- Localisation — `LocaleStore` with key lookup, plural forms, and runtime language switching

**Audio**
- `AudioManager` — music, SFX, volume, mute
- `PositionalAudio` — distance-based volume and stereo panning

**Animation**
- 30 easing functions, `Tween` for single-value animation
- `SpriteAnimation`, `AnimationPlayer` — frame-based sprite animation
- `AnimationStateMachine` — declarative state/transition/condition machine

**Debug & production**
- Debug overlay (F1) — FPS, scene stack, active flags
- Debug console (F3) — runtime log viewer
- `debug_log` — structured log with level/tag filtering
- `crash_guard` — context manager that writes a crash report on unhandled exceptions

---

## Quick start

```bash
pip install -e .
python run_examples.py   # interactive example launcher
python main.py           # run the default example
```

---

## Game template

Copy `game_template/` to start a new project:

```
game_template/
├── main.py                    ← entry point
├── assets/
│   └── theme.json             ← optional theme overrides
└── game/
    ├── actions.py             ← input action constants
    ├── locale/en.json         ← translation strings
    └── scenes/
        ├── main_menu.py
        ├── game_scene.py      ← stubbed with all systems commented out
        ├── pause_scene.py
        └── settings_scene.py  ← volume, fullscreen, key remapping
```

---

## Project structure

```
pygame_engine/        ← repo root
├── docs/             ← 30 architecture and system docs
├── examples/         ← 21 runnable examples (one per system)
├── game_template/    ← copy-and-start skeleton
├── tests/            ← 1083+ tests across 45 files
├── pygame_engine/    ← the importable package
├── main.py           ← dev entry point (uncomment an example)
├── run_examples.py   ← interactive example launcher
└── pyproject.toml
```

---

## Requirements

- Python 3.11+
- pygame-ce 2.4+

---

## Phases completed

| Phase | Systems |
|---|---|
| 1–8 | Runtime, scene stack, 15 UI widgets, layout, theme, input, assets, audio, animation, particles, persistence, debug, EventBus, transitions |
| 9 | Camera, Tilemap, Dialogue, Slider/Checkbox/RadioGroup |
| 10 | Screen manager, responsive layout, sprite atlas, localisation, crash logging |
| 11 | A* pathfinding, animation state machine, positional audio, 2D lighting |
| 12 | Key remapping, controller/joystick support, haptic feedback |
| 13 | File-driven JSON theming with live reload, RichLabel rich text |