# Theme System

## Purpose

Centralised visual styling for all widgets and scenes. Widgets look up
colours, sizes, and spacing from a single active theme rather than
hardcoding values.

---

## Quick start

```python
from pygame_engine.theme.runtime import get_theme, set_theme
from pygame_engine.theme.defaults import Theme

# Read current theme (in any widget or scene)
theme = get_theme()
colour    = theme.colours.bg_base
font_size = theme.typography.md
btn_bg    = theme.button.normal.bg

# Set a custom theme at startup
set_theme(Theme(...))   # or use theme_from_file()
```

---

## File-driven theming

Load a JSON file and override only the values you want to change:

```python
from pathlib import Path
from pygame_engine.theme.loader import theme_from_file, reload_theme_file
from pygame_engine.theme.runtime import set_theme

# Load once at startup
theme = theme_from_file(Path("assets/theme.json"))
set_theme(theme)

# Hot-reload during development (call on key press or file-watch event)
reload_theme_file(Path("assets/theme.json"))
```

### JSON format

Only include keys you want to override. All other values keep their defaults:

```json
{
    "colours": {
        "bg_base":   [20, 20, 28],
        "bg_raised": [30, 32, 44],
        "text":      [228, 228, 235]
    },
    "typography": {
        "family": "segoeui,helvetica,arial",
        "md": 18
    },
    "button": {
        "normal":  {"bg": [50, 85, 165], "radius": 6},
        "hovered": {"bg": [70, 115, 205]},
        "padding": 10
    },
    "panel": {
        "surface": {"bg": [28, 32, 44], "border": [55, 62, 85]},
        "padding": 16
    },
    "spacing": {
        "xl": 28
    }
}
```

### Generate a starter file from the current theme

```python
import json
from pygame_engine.theme.loader import theme_to_dict
from pygame_engine.theme.runtime import get_theme

print(json.dumps(theme_to_dict(get_theme()), indent=2))
```

---

## Theme structure

```
Theme
├── colours         ColoursTheme    — bg_dark, bg_base, bg_raised, text, text_secondary, border
├── typography      TypographyTheme — family, xs, sm, md, lg, xl, xxl
├── spacing         SpacingTheme    — xs, sm, md, lg, xl, xxl
├── button          ButtonTheme     — normal, hovered, pressed, disabled, text, text_disabled, padding
├── label           LabelTheme      — text, secondary_text
└── panel           PanelTheme      — surface, padding
```

Each `SurfaceStyle` has: `bg`, `border`, `border_width`, `radius`.
Each `TextStyle` has: `colour`, `font_size`, `font_family`, `bold`.

---

## Creating a custom theme

```python
from dataclasses import replace
from pygame_engine.theme.defaults import Theme, ColoursTheme, ButtonTheme, SurfaceStyle

custom = Theme(
    colours=ColoursTheme(
        bg_base=(18, 18, 26),
        text=(230, 230, 240),
    ),
    button=ButtonTheme(
        normal=SurfaceStyle(bg=(45, 80, 160), radius=8),
    ),
)
set_theme(custom)
```

Or extend the default:

```python
from copy import deepcopy
theme = deepcopy(DEFAULT_THEME)
theme.colours.bg_base = (18, 18, 26)
set_theme(theme)
```

---

## Accepted decisions

### Python dataclasses, not YAML/JSON as primary format
The Python theme is the source of truth — type-checked, IDE-navigable,
refactor-safe. The JSON loader is an optional overlay for designer workflow.

### `get_theme()` module-level accessor
Widgets are created in many places. Injection would require threading
a theme argument through every constructor. A stable global accessor
is the right tradeoff for a controlled-scope framework.

### Only overrides in JSON files
JSON files contain deltas, not full themes. This means new theme fields
added to the engine automatically get sensible defaults in all existing
JSON theme files without requiring updates.
