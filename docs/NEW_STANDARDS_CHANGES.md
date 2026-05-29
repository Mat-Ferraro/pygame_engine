**Generated from:** audit of pygame_engine/ and game/ against the
complete standards document set (CODING_STANDARDS, LOGGING_STANDARDS,
ACCESSIBILITY_STANDARDS, TYPE_ANNOTATION_STANDARDS, IMPORT_STANDARDS,
PERFORMANCE_BUDGETS, ERROR_MESSAGE_STANDARDS).

**This document is additive to CODEBASE_CHANGES.md.**
Changes already tracked there (C1–C13) are not repeated here.
This document covers the new violations surfaced by the new standards.

---

## How to Read This Document

Each change has:
- **What** — the specific problem
- **Where** — the files affected (with counts where widespread)
- **Standard** — which document requires the fix
- **Priority** — 1 (blocks new features), 2 (should fix soon), 3 (cleanup)

---

## Priority 1 — Blocks New Features or Correctness

---

### N1 — print() in Engine Public Modules

**What:** Four engine files use `print()` — forbidden in `pygame_engine/`
by LOGGING_STANDARDS.md.

**Where:**
- `pygame_engine/dialogue/runner.py:17-18` — `print()` in example
  lambdas at module level. These run when the module is imported.
- `pygame_engine/devtools/crash_log.py:64,66,81,83` — `print()` to stderr.
  These are intentional stderr output for crash reporting. This is a
  legitimate exception — `debug_log` cannot be used here because the
  crash reporter runs when the engine is broken. Document as an explicit
  exception with a comment.
- `pygame_engine/persistence/save_manager.py:34` — `print()` in what
  appears to be a debug helper or example. Remove or convert.
- `pygame_engine/theme/loader.py:125` — `print(json.dumps(...))` in the
  loader. Remove — this is leftover debug output.

**Action:**
- `crash_log.py` — add a comment: "print() to stderr is intentional here
  — debug_log cannot be used when the engine is in a crash state."
- `runner.py` — remove the module-level lambda examples or move them
  inside a function that is only called explicitly.
- `save_manager.py:34` — remove the print() call.
- `theme/loader.py:125` — remove the print() call.

**Standard:** LOGGING_STANDARDS.md Section 1
**Priority:** 1

---

### N2 — Reduced Motion Not Checked in Scene Animations

**What:** Two game scenes update `self._t` and use it for background
animations without checking `app.reduced_motion`. Under
ACCESSIBILITY_STANDARDS.md, all animations must respect this flag.

**Where:**
- `game/scenes/main_menu_scene.py:112` — `self._t += dt` drives a sine
  wave wood grain animation
- `game/scenes/game_hub_scene.py:233` — `self._t += dt` drives the same

**Action:**
```python
# In update():
if not self._app.reduced_motion:
    self._t += dt
# self._t stays 0.0 — background is static in reduced motion mode
```

The static background when `reduced_motion=True` must still be readable
— verify the scene looks correct with `self._t = 0.0`.

**Standard:** ACCESSIBILITY_STANDARDS.md Section 4
**Priority:** 1 — accessibility is a correctness concern, not cosmetic

---

## Priority 2 — Should Fix Before Building New Features

---

### N3 — Deprecated `Union` Import in Engine

**What:** `pygame_engine/particles/emitter.py` imports `Union` from
`typing`. This is deprecated in Python 3.10+ in favour of `|` syntax.
TYPE_ANNOTATION_STANDARDS.md requires built-in generic syntax.

**Where:** `pygame_engine/particles/emitter.py:46`

**Action:**
```python
# Before
from typing import Union
def some_fn(x: Union[int, float]) -> None: ...

# After
def some_fn(x: int | float) -> None: ...
```

Remove the `Union` import. Convert all `Union[X, Y]` usages in the file
to `X | Y`. Requires `from __future__ import annotations` at the top
if not already present.

**Standard:** TYPE_ANNOTATION_STANDARDS.md Section 3
**Priority:** 2

---

### N4 — `NamedTuple` Import — Review Required

**What:** `pygame_engine/devtools/debug_log.py:22` imports `NamedTuple`
from `typing`. `NamedTuple` is not deprecated and cannot be replaced
with built-in syntax — this is not a violation. However, confirm the
import is still needed and not a leftover.

**Where:** `pygame_engine/devtools/debug_log.py:22`

**Action:** Confirm `NamedTuple` is actively used in `debug_log.py`. If
it is, add it to the "permitted typing imports" exception list in
TYPE_ANNOTATION_STANDARDS.md. If not, remove it.

**Standard:** TYPE_ANNOTATION_STANDARDS.md Section 3
**Priority:** 2 — verification only

---

### N5 — Aliased Internal Imports in application.py

**What:** `application.py` aliases two imports with underscore-prefixed
names:
```python
from pygame_engine.events.event_bus import bus as _event_bus
from pygame_engine.state.runtime_flags import flags as _runtime_flags
```

These are not standard aliases — they are aliased to private names to
signal internal use. IMPORT_STANDARDS.md prohibits invented aliases.
The correct approach is to use the module-level singletons directly
without aliasing, or to give them clearer names.

**Where:** `pygame_engine/app/application.py:33,37`

**Action:** Remove the aliases. Use `bus` and `flags` directly. If name
collision is a concern, restructure the import to use the module namespace:
```python
from pygame_engine.events import event_bus as _event_bus_module
# use _event_bus_module.bus
```

Or accept `bus` and `flags` as the local names — they are clear enough.

**Standard:** IMPORT_STANDARDS.md Section 2
**Priority:** 2

---

### N6 — `fn` Parameter Name in Public Migration API

**What:** `pygame_engine/persistence/migrations.py` has two public
methods with a parameter named `fn` — a banned abbreviation in public
identifiers.

**Where:**
- `migrations.py:96` — `decorator(fn)` in a public decorator function
- `migrations.py:105` — `register_fn(fn)` public method

**Action:**
```python
# Before
def register_fn(fn: Callable) -> None: ...

# After
def register_handler(handler: Callable) -> None: ...
```

Rename `fn` → `handler` or `callback` depending on the semantics.
Update all callers and tests.

**Standard:** CODING_STANDARDS.md Section 4, RESTRICTIONS.md R16
**Priority:** 2

---

### N7 — `__init__` Missing `-> None` in Two Engine Files

**What:** Two public `__init__` methods lack the required `-> None`
return annotation.

**Where:**
- `pygame_engine/state/runtime_flags.py:39`
- `pygame_engine/ui/feedback/confirm_dialog.py:116`

**Action:** Add `-> None` to both:
```python
def __init__(self, ...) -> None:
```

**Standard:** TYPE_ANNOTATION_STANDARDS.md Section 10
**Priority:** 2

---

### N8 — Colour-Only Signals in Game UI

**What:** Several places in game scenes use colour as the only
signal for status — `STAMP_OK`, `STAMP_WARN`, `STAMP_DANGER` applied
to coloured backgrounds or text with no accompanying text or icon
differentiator. ACCESSIBILITY_STANDARDS.md Section 3 requires that
colour never be the only signal.

**Where:**
- `management_scene.py:516-518` — row backgrounds coloured danger/warn
  with no text indicator
- `management_scene.py:543` — satisfaction colour with no label
- `management_scene.py:385` — EXPIRING coloured warning with no icon

These affect all scenes that use `_grade_col()` for colour-only
grade representation.

**Action:** Each colour-coded status must include a text label or symbol:
```python
# Before — colour only
surface.blit(font.render(hero.name, True, _grade_col(hero.grade)), pos)

# After — colour + text
grade_label = f"[{hero.grade}] {hero.name}"
surface.blit(font.render(grade_label, True, _grade_col(hero.grade)), pos)
```

For row backgrounds, add a small text indicator ("!", "✓", "⚠") in
the row rather than relying solely on background colour.

**Standard:** ACCESSIBILITY_STANDARDS.md Section 3
**Priority:** 2

---

## Priority 3 — Cleanup (No Feature Blocked)

---

### N9 — 184 Public Engine Methods Without Docstrings

**What:** 184 public methods across the engine lack docstrings.
This is the largest single gap identified by the audit.

**Where (by file — worst offenders):**
- `animation/easing.py` — all 30 easing functions lack docstrings
- `animation/animator.py` — all property accessors lack docstrings
- Various widget property accessors throughout `ui/`

**Breakdown by urgency within Priority 3:**

*Most critical to document first* (foundational systems users depend on):
- `state/observable.py` — all public methods
- `scene/scene_manager.py` — push, pop, replace, push_with, pop_with
- `app/application.py` — run, stop, all system properties
- `events/event_bus.py` — on, emit, off, once

*Medium* (commonly used widgets):
- All widget `render()`, `handle_event()`, `update()` methods

*Low* (property accessors where name is self-documenting):
- `animation/animator.py` properties — `name`, `frames`, `loop`
- Easing functions — a single module docstring explaining the pattern
  may be sufficient rather than one per function

**Action:** Address in the order above, starting with `observable.py`
before Phase 1 development begins (the Observable upgrade will change
these methods anyway — document the new interface, not the old one).

**Standard:** CODING_STANDARDS.md Section 2, RESTRICTIONS.md R15
**Priority:** 3

---

### N10 — 8 Public Classes Without Docstrings

**What:** 8 public classes lack class-level docstrings.

**Where:**
- `debug/debug_log.py:25` — `class LogLevel`
- `debug/debug_log.py:31` — `class LogEntry`
- `theme/tokens.py:69` — `class Colours`
- `theme/tokens.py:80` — `class Spacing`
- `theme/tokens.py:93` — `class Typography`
- `theme/tokens.py:96` — `class Radii`
- `theme/tokens.py:103` — `class Borders`
- `theme/tokens.py:112` — `class Timing`

**Action:** The `tokens.py` classes are theme data containers — a single
line docstring per class is sufficient:
```python
class Colours:
    """Theme colour palette — background, foreground, and accent colours."""
```

**Standard:** CODING_STANDARDS.md Section 2.1
**Priority:** 3

---

### N11 — 94 Uses of `sw`/`sh` in Game Scenes

**What:** Game scene render methods use `sw, sh = surface.get_size()`
throughout — 94 occurrences across 8 files.

**Where:** All game scenes in `render()` and `_draw_*()` methods.

**Action:** This is a game-layer variable inside private methods — not
a public API violation. The standard applies most strictly to public
identifiers. However, for readability, convert to:
```python
surface_width  = surface.get_width()
surface_height = surface.get_height()
```

Or where both are needed frequently, store once at the top of `render()`:
```python
surface_width, surface_height = surface.get_size()
# But use descriptive names, not sw/sh
```

**Standard:** CODING_STANDARDS.md Section 4
**Priority:** 3 — game layer, private methods, low urgency

---

### N12 — `col` Ambiguity in Game Scenes

**What:** `col` is used to mean both "colour" (a tuple) and "column
position" (an int) in several game scenes. This is the specific
ambiguity the naming standard was written to prevent.

**Where:** 15+ occurrences across game scene files. Most are `col` as
colour in `stat_row()` helper functions.

**Action:** Rename consistently:
- `col` meaning colour → `colour`
- `col` meaning column x-position → `column_x`

**Standard:** CODING_STANDARDS.md Section 4
**Priority:** 3

---

### N13 — Game Files Over the Soft Limit Not Tracked in CODEBASE_CHANGES.md

**What:** Three game files are over the 400-line soft limit and not
yet tracked as needing decomposition.

**Where:**
- `campaign_map_scene.py` — 441L (soft limit)
- `mission_assignment_scene.py` — 548L (soft limit, close to hard cap)
- `training_scene.py` — 415L (soft limit)

Note: `management_scene.py` (882L hard cap) and `game_hub_scene.py`
(619L hard cap) are already tracked as C4 and C6 in CODEBASE_CHANGES.md.
`inventory_scene.py` (532L) is tracked as C7. These three are new.

**Action:** Add to CODEBASE_CHANGES.md as C14, C15, C16. Decompose
when new features are added to these files, or when the hard cap is
reached.

**Standard:** RESTRICTIONS.md R17, CODING_STANDARDS.md Section 5
**Priority:** 3

---

### N14 — Keyboard Navigation Gap: Dropdown Widget

**What:** The `Dropdown` widget does not appear in the interactive
widget list in ACCESSIBILITY_STANDARDS.md — verify it has complete
keyboard support.

**Where:** `pygame_engine/ui/controls/dropdown.py`

**Action:** From the test suite (`test_dropdown.py`), the dropdown
has arrow key navigation, Enter to select, and Escape to close. This
is correct. Add `Dropdown` to the keyboard navigation table in
ACCESSIBILITY_STANDARDS.md to confirm it is documented.

**Standard:** ACCESSIBILITY_STANDARDS.md Section 2
**Priority:** 3 — documentation gap only, implementation is correct

---

## Summary Table

| ID  | Change                                 | Priority | Standard               | Scope  |
|-----|----------------------------------------|----------|------------------------|--------|
| N1  | Remove print() from engine modules     | 1        | LOGGING                | Engine |
| N2  | Reduced motion in scene animations     | 1        | ACCESSIBILITY          | Game   |
| N3  | Replace Union with | syntax            | 2        | TYPE_ANNOTATIONS       | Engine |
| N4  | Verify NamedTuple import               | 2        | TYPE_ANNOTATIONS       | Engine |
| N5  | Remove aliased internal imports        | 2        | IMPORT_STANDARDS       | Engine |
| N6  | Rename fn parameter in migrations      | 2        | CODING_STANDARDS R16   | Engine |
| N7  | Add -> None to two __init__ methods    | 2        | TYPE_ANNOTATIONS       | Engine |
| N8  | Add text to colour-only UI signals     | 2        | ACCESSIBILITY          | Game   |
| N9  | 184 public methods need docstrings     | 3        | CODING_STANDARDS R15   | Engine |
| N10 | 8 public classes need docstrings       | 3        | CODING_STANDARDS R15   | Engine |
| N11 | 94 sw/sh uses in game scenes           | 3        | CODING_STANDARDS R16   | Game   |
| N12 | col ambiguity in game scenes           | 3        | CODING_STANDARDS R16   | Game   |
| N13 | 3 game files over soft limit           | 3        | RESTRICTIONS R17       | Game   |
| N14 | Add Dropdown to accessibility table    | 3        | ACCESSIBILITY          | Docs   |

---

## Combined Priority Order with Existing Changes

Including the existing C1–C13 from CODEBASE_CHANGES.md, the full
recommended sequence is:

**Do immediately (before any Phase 1 work):**
1. N1 — remove print() from engine (30 min)
2. N2 — add reduced_motion check to scene animations (15 min)
3. C8 — Observable[T] upgrade (multi-session — foundation for everything)
4. C1 — theme singleton removal (depends on C8)

**Do before building the editor (Phase 2–3):**
5. N3 — replace Union with | syntax (15 min)
6. N7 — add -> None to two __init__ methods (5 min)
7. N6 — rename fn parameter in migrations (30 min)
8. N5 — remove aliased imports in application.py (15 min)
9. C2 — move shared UI out of management_scene.py
10. C3 — ConfirmDialog circular import
11. C5 — scene navigation via registry

**Cleanup (ongoing, no deadline):**
12. N8 — colour-only UI signals (game scenes)
13. N9 — docstring coverage (start with observable.py)
14. N10 — class docstrings (tokens.py, debug_log.py)
15. C4 — management_scene decomposition
16. C6 — game_hub_scene decomposition
17. N11 — sw/sh rename in game scenes
18. N12 — col ambiguity rename
19. N13 — add C14/C15/C16 to CODEBASE_CHANGES.md
20. N4 — verify NamedTuple import
21. N14 — update accessibility docs table
---

## Resolution Status

Updated after Audits #1, #2, and #3.

### Resolved — Engine fixes applied

| Item | Resolution |
|---|---|
| N1 — print() in engine | Fixed — inspector returns string, runner uses pass, save_manager/loader cleaned up, crash_log documented |
| N3 — Union syntax | Fixed — emitter.py uses \| syntax, from __future__ import annotations added |
| N4 — NamedTuple import | Verified — NamedTuple is in active use in debug_log.py, not a violation |
| N5 — Aliased imports | Fixed — application.py aliases removed |
| N6 — fn parameter | Fixed — renamed to migration_fn in migrations.py |
| N7 — __init__ -> None | Fixed — runtime_flags.py and confirm_dialog.py both updated |
| N9 — 184 docstrings | Fixed — reduced to 3 genuine gaps (tileset, layer_names, is_controller_button_down) |
| N10 — 8 class docstrings | Fixed — all 8 classes documented |

### Resolved — Game template fixes applied

| Item | Resolution |
|---|---|
| N2 — reduced_motion | Fixed — comment added to game_scene.py update() method |

### Deferred — Game layer, no engine violation

These items apply to game code (hero_management_engine), not to pygame_engine itself.
They are not engine violations and are tracked here for awareness only.

| Item | Status |
|---|---|
| N8 — colour-only UI signals | Deferred to game code work — use text/icon alongside colour |
| N11 — sw/sh in game scenes | Deferred — private render method variables, low urgency |
| N12 — col ambiguity | Deferred — rename when touching affected files |
| N13 — game files over soft limit | Tracked in CODEBASE_CHANGES.md C4, C6, C7, C13 |

### Minor / Docs

| Item | Status |
|---|---|
| N14 — Dropdown in accessibility table | Dropdown keyboard support confirmed correct — add to ACCESSIBILITY_STANDARDS.md when convenient |