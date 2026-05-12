## Purpose

The theme system defines how the engine expresses visual style in a reusable, structured way.

The theme system should allow:
- consistent styling across widgets
- clean defaults
- project-level overrides
- separation between design tokens and resolved runtime values

---

## Accepted Core Decisions

The theme system currently assumes:

- widgets may access styling through a stable runtime theme interface
- theme values should not be hardcoded throughout widgets
- engine defaults should exist and be overridable
- local/widget-specific overrides may be added later if useful

---

## Current Theme Modules

The theme package currently contains:

- `tokens.py`
- `defaults.py`
- `runtime.py`

Suggested roles:
- `tokens.py` = raw design tokens
- `defaults.py` = default theme definitions
- `runtime.py` = active theme object and theme lookup behavior

---

## Theme Design Principles

1. Widgets should not hardcode magic numbers and colors everywhere.
2. Theme values should be centralized and overridable.
3. Tokens should be reusable across many widgets.
4. Runtime theme access should be predictable and lightweight.
5. Game projects should be able to override appearance without changing widget logic.

---

## Theme Layers

### Tokens
The smallest design values:
- colors
- spacing
- font sizes
- radii
- border widths
- timing constants

### Defaults
A coherent default theme built from tokens.

### Runtime
The active resolved theme object used during app execution.

---

## What Belongs in Tokens

Examples:
- color palette values
- spacing scale
- typography scale
- radius scale
- shadow values if supported
- standard timing values for UI transitions

Tokens should be:
- reusable
- generic
- stable

Tokens should not contain widget-specific behavior logic.

---

## What Belongs in Defaults

`defaults.py` should define the engine’s baseline theme.

This can include:
- default button style values
- default panel background/border values
- default text styles
- default tooltip/toast styles
- default spacing relationships

Defaults should translate raw tokens into practical engine styles.

---

## What Belongs in Runtime

`runtime.py` should expose the currently active theme data.

Possible responsibilities:
- store the current theme
- resolve style lookups
- provide theme access helpers
- support theme swapping if needed later

Recommended rule:
- runtime should be the access point, not the source of raw token truth

---

## Widget Styling Model

Accepted direction:
- widgets may access the active theme through a stable runtime interface
- style keys should remain explicit
- local overrides may be added later

This is intentionally simpler than a fully injected style graph for version one.

---

## Theme Categories

The runtime theme should support categories such as:
- colors
- typography
- spacing
- surfaces
- borders
- controls
- feedback widgets

Examples:
- button normal/hover/pressed/disabled styles
- panel fill/border styles
- label text color/size defaults
- tooltip background/text styles

---

## Override Strategy

Projects using `pygame_engine` should be able to:
- use engine defaults directly
- override some theme values
- replace the whole default theme if desired

Recommended rule:
- use shallow, explicit override paths
- avoid undocumented hidden theme keys

---

## Theme Lookup Direction

Possible usage:
```python
theme = app.theme
button_style = theme.controls.button.primary
```

The exact API can change, but runtime theme access should be:
- discoverable
- structured
- easy to autocomplete if typed later

---

## Hardcoding Rules

Avoid hardcoding in widgets:
- RGB tuples
- font sizes
- border thickness
- spacing values

Allowed exceptions:
- temporary prototyping
- debug-only visuals
- isolated tests/examples

Even then, those should usually be migrated into theme values.

---

## Relationship to `utils/colors.py`

`utils/colors.py` may still contain low-level color helpers:
- color interpolation
- clamp helpers
- conversion helpers

But actual visual identity values should live in `theme`, not `utils`.

---

## Rules for Future Development

1. Tokens define reusable values.
2. Defaults define the engine’s baseline look.
3. Runtime exposes active theme access.
4. Widgets should be theme-aware, not theme-hardcoded.
5. Theme keys should remain documented and stable.

---

## Open Questions

- Should theme values be plain dictionaries, dataclasses, or typed objects?
- Should widgets cache resolved style values?
- Should theme changes at runtime be supported?
- How should local widget style overrides interact with the active theme?
