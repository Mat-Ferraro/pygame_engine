# pygame_engine — Coding Standards

**Version:** 2.0-design
**Authority:** Supplements ARCHITECTURE.md and RESTRICTIONS.md

This document defines the coding standards for pygame_engine and all
projects built with it. Standards here are enforceable — either by
automated tooling (ruff, pydocstyle) or by code review with a clear
criterion.

When a standard conflicts with a restriction, the restriction wins.

---

## 1. The Fundamental Distinction

Before all other rules — the boundary between docstrings and comments
must be clear. They serve different audiences.

**Docstrings** are for consumers of the code — developers using the API
without reading the implementation.
Answers: what is this, what does it promise, what does it need, what can go wrong.
Appears in IDE tooltips and auto-generated documentation.

**Comments** are for maintainers of the code — developers reading or
changing the implementation.
Answers: why this approach, why not the alternative, why this invariant must hold.
Never appears in generated documentation.

The same information must never appear in both. Contract information
belongs in docstrings. Implementation decisions belong in comments.

---

## 2. Docstrings

### 2.1 When to Write One

**Always required:**
- Every public class in the stable API tier
- Every public method in the stable API tier
- Every public module in pygame_engine/
- Every public function in utility modules (text_utils, mathx, colors, rects)

**Required when the name is not self-documenting:**
- Any method whose purpose is not immediately obvious from its name alone
- Any method with non-obvious parameter constraints or interactions
- Any method with a non-obvious return value

**Not required:**
- Private methods prefixed with _ (use a comment if explanation is needed)
- Methods that override a parent and add no new behaviour
- Simple properties where the class docstring already explains the property
- Test functions — test names must be self-documenting

```python
# Required — public API, non-obvious contract
def truncate(font, text, max_width, ellipsis="…") -> str:
    """..."""

# Required — public class
class Observable(Generic[T]):
    """..."""

# Not required — private helper
def _build_surface(self) -> pygame.Surface:
    # Constructs the cached surface from current state.
    # Called on first render and whenever _dirty is True.
    ...

# Not required — obvious override adding no new contract
def update(self, dt: float) -> None:
    super().update(dt)
    self._t += dt
```

---

### 2.2 Format — Google Style

We use Google style throughout. It is readable, concise, and natively
supported by pdoc (our documentation generator) and most IDEs.

**Module docstring:**
```python
"""
Text layout utilities for pygame_engine.

Provides three standalone functions for fitting text into constrained
widths. Pure functions — no widgets, no theme access, no state.

Usage::

    from pygame_engine.graphics.text_utils import truncate, wrap_text

    font = pygame.font.SysFont(None, 22)
    line = truncate(font, hero.name, max_width=300)
    lines = wrap_text(font, description, max_width=400)
"""
```

**Class docstring:**
```python
class Observable(Generic[T]):
    """
    A value that notifies subscribers when it changes.

    Subscribers are held via weak references — destroying a subscriber
    automatically unsubscribes it without explicit cleanup.

    Use Observable for reactive values UI elements should track.
    Use EventBus for discrete events between loosely coupled systems.

    Example::

        gold = Observable(500)
        gold.subscribe(lambda old, new: print(f"{old} -> {new}"))
        gold.set(450)  # prints "500 -> 450"

    Note:
        Calling set() with the current value does not notify subscribers.
        Use transaction() when making multiple related changes to fire
        a single notification rather than one per change.
    """
```

**Method docstring — full form:**
```python
def truncate(
    font:      pygame.font.Font,
    text:      str,
    max_width: int,
    ellipsis:  str = "…",
) -> str:
    """
    Truncate text to fit within max_width pixels.

    If the text already fits it is returned unchanged. Otherwise characters
    are removed from the right and the ellipsis appended until the result
    fits. The result is guaranteed to fit within max_width pixels unless
    max_width is smaller than the ellipsis itself.

    Args:
        font:      Font used to measure pixel widths.
        text:      Source string to truncate.
        max_width: Maximum allowed width in pixels. Zero or negative
                   returns the ellipsis string.
        ellipsis:  Suffix appended when truncation occurs. Default "…".

    Returns:
        The original string if it fits, otherwise a truncated string
        ending with the ellipsis that fits within max_width pixels.

    Raises:
        TypeError: If font is not a pygame.font.Font instance.

    Postcondition:
        font.size(result)[0] <= max(max_width, font.size(ellipsis)[0])

    Example::

        truncate(font, "The quick brown fox", max_width=80)
        # → "The quick bro…"

        truncate(font, "Short", max_width=1000)
        # → "Short"  (unchanged — already fits)
    """
```

**Method docstring — short form (when contract is simple):**
```python
def set_silent(self, value: T) -> None:
    """Set the value without notifying subscribers."""

def clear_focus(self) -> None:
    """Remove focus from all widgets. No ui.focus.changed event is emitted."""

def dispose(self) -> None:
    """
    Cancel all subscriptions in this group.

    Idempotent — calling dispose() multiple times does not raise.
    After disposal, add() becomes a no-op.
    """
```

---

### 2.3 The Docstring Sections

**Summary line** — always. One sentence. One line. Fits within 88 characters.
Use the imperative mood: "Return the…", "Register a…", "Remove focus from…"
Fragments do not end with a period. Full sentences do.
Prefer the fragment form.

```python
# Fragment (preferred)
"""Remove focus from all widgets."""

# Full sentence (when needed for clarity)
"""This method is called automatically by Scene.on_exit()."""
```

**Extended description** — when the summary alone is insufficient.
Explains important behaviour, tradeoffs, constraints. Not a restatement
of the summary.

**Args** — when parameters have non-obvious constraints or meanings.
Skip the section entirely if all parameters are self-documenting.

```python
# Args not needed — self-evident from name and type
def set_volume(self, volume: float) -> None:
    """Set the bus volume. Clamped to 0.0–1.0."""

# Args needed — constraint not obvious from type annotation alone
def subscribe(self, callback: Callable[[T, T], None]) -> Token:
    """
    Register a callback to be called when the value changes.

    Args:
        callback: Called with (old_value, new_value). Held via weak
                  reference — the callback must remain alive for
                  notifications to fire.
    """
```

**Returns** — when the return value is not obvious from name and return type.
Not needed when the name already communicates the return value.

**Raises** — only exceptions callers should handle or that indicate API
misuse. Do not document internal exceptions callers cannot act on.
Do not document TypeError for obviously wrong types — that is Python's job.

**Postcondition** — when the guarantee after the call is non-obvious and
important for correctness. Especially valuable for Observable,
SubscriptionGroup, and CommandStack where undo correctness depends on it.

```python
def dispose(self) -> None:
    """
    Cancel all subscriptions in this group.

    Postcondition:
        After dispose(), no callbacks in this group will ever fire.
        add() is a no-op. The method is idempotent.
    """
```

**Note** — important caveats, performance characteristics, threading
considerations. Use sparingly — if important enough to be a Note it is
probably important enough to be in the main description.

**Example** — when the API has non-obvious usage patterns. Use :: before
the code block (Google style). One focused example is better than three
variations. Not needed for obvious methods.

---

### 2.4 One-Line vs Multi-Line

If the entire docstring fits on one line including quotes — write it on
one line:
```python
def dispose(self) -> None:
    """Cancel all subscriptions in this group."""
```

If it needs more than one line — use multi-line form. Summary line first,
blank line before sections:
```python
def subscribe(self, callback) -> Token:
    """
    Register a callback to be called when the value changes.

    Args:
        callback: Called with (old_value, new_value).
    """
```

Never write a one-liner that wraps past 88 characters:
```python
# Bad — too long, should be multi-line
def subscribe(self, callback: Callable[[T, T], None]) -> Token:
    """Register a callback that will be called with old and new value when the observable changes."""
```

---

### 2.5 What Never Belongs in a Docstring

**Do not restate type annotations:**
```python
# Bad — the annotation already says this
def set(self, value: T) -> None:
    """
    Args:
        value (T): The new value to set.
    """

# Good — adds information the annotation does not provide
def set(self, value: T) -> None:
    """
    Args:
        value: If equal to the current value, no notification fires.
    """
```

**Do not describe the implementation:**
```python
# Bad — describes how, not what
def truncate(font, text, max_width) -> str:
    """Uses binary search to find the longest prefix that fits."""

# Good — describes the contract
def truncate(font, text, max_width) -> str:
    """Truncate text to fit within max_width pixels."""
```

**Do not write summaries less informative than the name:**
```python
# Bad — adds nothing
def clear_focus(self) -> None:
    """Clears the focus."""

# Good — adds the non-obvious detail
def clear_focus(self) -> None:
    """Remove focus from all widgets. No ui.focus.changed event is emitted."""
```

**Do not use past tense. Use the imperative:**
```python
# Bad
"""Returned the truncated string."""

# Good
"""Return the truncated string."""
```

**Do not write paragraph-length summary lines:**
```python
# Bad
def subscribe(self, callback) -> Token:
    """Registers a callback function that will be called every time the
    observable value changes, passing both the old value and the new
    value to the callback as arguments."""

# Good
def subscribe(self, callback) -> Token:
    """Register a callback to be called when the value changes."""
```

---

### 2.6 Docstring Frequency by Location

| Location | Requirement |
|---|---|
| pygame_engine/ public module | Required: module, every public class, every public method |
| pygame_engine/_internal/ | Module docstring required. Class/method docstrings encouraged |
| game/ scenes and systems | Class docstrings encouraged. Methods only where non-obvious |
| tests/ | None. Test names must be self-documenting |
| __init__.py files | One-line docstring stating what the package provides |

---

## 3. Comments

### 3.1 The Core Principle

Explain why, not how. The how is readable from the code. The why is not.

```python
# Bad — describes what the code obviously does
self._dirty = True  # mark as dirty

# Good — explains the reason
# Rect change invalidates the cached surface. render() rebuilds on the
# next frame when _dirty is True. Avoids calling font.render() every frame.
self._dirty = True
```

---

### 3.2 Required Comment Situations

**Workarounds** — what the limitation is, why this approach, where the fix lives:
```python
# _Adapter is created lazily inside push() rather than at class definition
# time to avoid a circular import between ui/ and scene/. ConfirmDialog
# lives in ui/ but must push onto SceneManager which lives in scene/.
# If Scene were imported at the top of this file, ui/ would need to import
# from scene/ creating a cycle. The lazy class creation breaks the cycle.
# TODO(restriction=C3): Replace with SceneLike protocol.
# See CODEBASE_CHANGES.md C3.
class _Adapter(Scene):
    ...
```

**Invariants** — properties that must always hold for correctness:
```python
class SceneStack:
    def __init__(self):
        self._stack: list[Scene] = []
        # INVARIANT: _stack is never empty while the application is running.
        # Application.run() pushes the initial scene before the game loop.
        # pop() checks len > 1 before removing. Violation causes IndexError
        # on _stack[-1] in render() and update().
```

**Magic numbers** — every constant not self-evidently named:
```python
# Bad
MAX_STACK_DEPTH = 8
GRID_SIZE = 8

# Good
# 8 covers: game -> pause -> inventory -> confirmation dialog and any
# reasonable modal nesting. Beyond this something is architecturally wrong.
# Configurable via AppConfig. See ARCHITECTURE.md Section 3.5.
MAX_STACK_DEPTH = 8

# 8px is the standard UI grid unit — divides evenly into common screen
# widths (1920, 1280, 960) and matches most design systems. Widgets snap
# to this grid in the editor.
GRID_SIZE = 8
```

**Intentional asymmetry** — when code looks wrong but is correct:
```python
# Event routing is reverse child order. Rendering is forward child order.
# Deliberately opposite — last-added widget renders on top visually and
# must also receive events first. Changing either direction breaks
# modal dialogs. See decision_log.md "Panel event routing".
for child in reversed(self._children):
    if child.handle_event(event):
        return True

for child in self._children:
    child.render(surface)
```

**Defensive notes** — preventing "obvious improvements" that would break things:
```python
# Do NOT use id(widget) as registry key. Python's id() is not stable
# across scene reconstructions — the same address can reuse after GC.
# Use widget.widget_id (a stable string) instead.
registry[widget.widget_id] = widget

# Do NOT change this to forward iteration. See comment above render().
for child in reversed(self._children):

# Do NOT call super().on_exit() before dispose(). The base class calls
# dispose() itself. Calling it here first causes a double-free in the
# weak reference registry.
super().on_exit()
```

**Algorithm and performance rationale** — when the approach is non-obvious:
```python
# Binary search rather than linear scan. Truncating a 500-character
# string character by character is 500 font.size() calls. Binary search
# is ~9 calls. This matters in render() which runs every frame.
#
# The +1 in (lo + hi + 1) // 2 is a standard upper-bound binary search
# trick to prevent infinite loops when lo + 1 == hi.
lo, hi = 0, len(text)
while lo < hi:
    mid = (lo + hi + 1) // 2
```

**Contract boundary** — where layers meet or ownership changes:
```python
def render(self, surface: pygame.Surface) -> None:
    # Everything below draws to surface and has no other side effects.
    # This method must remain pure given self's current state — R10.
    # Do not read pygame.time.get_ticks() here. Use self._t set in update().
```

**"Why not" comments** — when the obvious alternative was rejected:
```python
# We use weakrefs for subscriber storage, not strong references.
# Strong references prevent garbage collection of subscriber objects —
# the most common memory leak in event-driven systems. The cost is a
# liveness check on each notification call. Benchmarks show <0.01ms
# per 1000 notifications — acceptable.

# We do NOT use asyncio for the debug server despite it being idiomatic.
# Asyncio requires an async game loop or a separate event-loop thread.
# A blocking thread with a lock is simpler for a read-only, low-frequency
# tool where async overhead provides no benefit.
```

---

### 3.3 TODO Format

Unformatted TODOs are noise. A TODO without context is useless six months later.

**Required format:**
```python
# TODO(tag): What needs to change.
# Why it has not been done now. Reference to document or ticket.
```

**Tags:**
```
TODO(restriction=C3)  — blocked by a codebase change in CODEBASE_CHANGES.md
TODO(phase=2)         — planned for a specific implementation phase
TODO(perf)            — performance improvement, not currently urgent
TODO(cleanup)         — code quality improvement
TODO(bug)             — known incorrect behaviour with workaround in place
```

**Examples:**
```python
# TODO(restriction=C1): Remove direct get_theme() call.
# Theme access must go through Application once the singleton is removed.
# See CODEBASE_CHANGES.md C1.
theme = get_theme()

# TODO(phase=2): Replace with FocusManager.next_focus() once it exists.
# Current implementation duplicates traversal logic across panels.
# See IMPLEMENTATION_ORDER.md Phase 2.1.
self._advance_focus_manually()

# TODO(perf): O(n) font measurements in the worst case.
# Acceptable for short strings. If profiling shows this is hot,
# switch to binary search as used in truncate().
while text and font.size(text)[0] > max_width:
    text = text[:-1]

# TODO(bug): Scroll position resets on every layout rebuild.
# The descriptor does not preserve scroll state across _build_layout() calls.
# Workaround: none. Tracked for Phase 3 StatefulWidget implementation.
```

---

### 3.4 Section Headers in Long Methods

Long render and build methods benefit from visible section headers.
Use this style consistently:

```python
def render(self, surface: pygame.Surface) -> None:
    surface_width  = surface.get_width()
    surface_height = surface.get_height()

    # -- Background ---------------------------------------------------
    surface.fill(DESK_BG)
    self._draw_wood_grain(surface, surface_width, surface_height)

    # -- Panels -------------------------------------------------------
    self._draw_panel(surface, self._rect_recruits, "Available Recruits")
    self._draw_panel(surface, self._rect_roster,   "Current Roster")

    # -- Content ------------------------------------------------------
    self._draw_recruit_list(surface)
    self._draw_roster_list(surface)

    # -- Overlays (must be last — renders above everything else) ------
    self._tab_bar.draw(surface)
    super().render(surface)
```

Use section headers when a method has three or more distinct phases.
Do not use them for short methods — they add noise without benefit.

---

### 3.5 Comment Proximity Rule

A comment belongs immediately above the code it explains.
Never below it. Never separated from it by a blank line.

```python
# Bad — blank line separates comment from what it explains
result = compute_something()

# The +1 prevents an off-by-one in the boundary case
adjusted = result + 1

# Good — immediately above what it explains
# +1 prevents off-by-one when result equals the upper boundary.
# Without it, boundary values are excluded from the valid range.
adjusted = result + 1
```

---

### 3.6 What Never Needs a Comment

```python
i += 1                          # increment i            <- never
self._dirty = True              # mark dirty             <- never
return False                    # return False           <- never
hero_count = len(self._state.roster)  # count the heroes  <- never
```

If the code is readable — well-named variables, clear structure, following
established patterns — it does not need a comment. The signal-to-noise ratio
of comments matters as much as coverage. Ten precise comments are more
valuable than fifty redundant ones.

---

### 3.7 Docstrings and Comments Together — The Correct Split

The most common mistake: implementation details in the docstring, or
contract information in a comment. The correct split:

```python
def set(self, value: T) -> None:
    """
    Set the value and notify subscribers if it changed.

    Postcondition:
        If value != previous value, all live subscribers have been called
        with (old_value, new_value). If equal, no subscribers are called
        and self.value is unchanged.
    """
    # Equality check before assignment avoids unnecessary subscriber calls.
    # High-frequency observables (mouse position, frame counter) benefit
    # significantly — the subscriber loop is skipped entirely when unchanged.
    if value == self._value:
        return

    old = self._value
    self._value = value

    # Iterate a snapshot of _subscribers in case a callback modifies
    # the list during notification (e.g. a subscriber unsubscribes itself).
    # Modifying a list while iterating it produces undefined behaviour.
    for ref in list(self._subscribers):
        callback = ref()
        if callback is not None:
            callback(old, value)
```

The docstring tells callers what they can depend on.
The comments tell maintainers why the implementation is written this way.
Neither duplicates the other.

---

## 4. Naming

Full rules in RESTRICTIONS.md R16. Summary here for reference.

**Classes:** PascalCase. No abbreviations. SceneManager not ScnMgr.

**Methods and properties:** snake_case.
Verbs for actions: subscribe(), dispose(), set_focus().
Nouns for properties: value, focused, children.
Booleans: is_visible, has_focus, can_subscribe, should_redraw.

**Events:** Dot-separated, noun-first.
engine.scene.changed, ui.focus.moved, audio.bus.muted.
Never on_scene_changed — the on_ prefix is for callback parameters, not events.

**Files:** snake_case.py. One primary class per file, file named after the class.

**Constants:** UPPER_SNAKE_CASE. No inline magic numbers.

**No abbreviations in public identifiers:**
Banned in public API: sw, sh, btn, cb, fn, idx, col (when ambiguous).
Permitted standard terms: dt, fps, ui, x/y/w/h.
Internal render methods may use short names — not public API.

---

## 5. File and Test Naming

### 5.1 Test Files

Test files are named after what they test, not when they were written
or which development phase added them. The name must remain accurate
as the code changes over time.

**Rule:** test_{module_or_class_name}.py

```
test_observable.py          correct — names the system under test
test_scene_manager.py       correct
test_text_utils.py          correct — covers truncate, wrap_text, wrap_and_truncate
test_audio_buses.py         correct — covers AudioBus and bus topology
test_phase14.py             WRONG — names a phase, not a system
test_new_widgets.py         WRONG — becomes misleading as the code evolves
test_refactor_march.py      WRONG — names a calendar event
```

For files covering multiple related things from the same module:
```
test_text_utils.py          covers truncate, wrap_text, wrap_and_truncate
test_audio_buses.py         covers AudioBus and AudioManager bus topology
```

Test function names follow the same principle:
```python
# Correct — names the behaviour
def test_subscribe_fires_on_value_change(): ...
def test_dispose_cancels_all_subscriptions(): ...
def test_transaction_fires_single_event(): ...

# Wrong — names a phase or sequence
def test_phase14_badge_renders(): ...
def test_new_observable_behaviour(): ...
```

### 5.2 Example Files

Example files are named after what they demonstrate.

**Rule:** example_{what_it_demonstrates}.py

```
example_observable.py            correct
example_tab_navigation.py        correct
example_ui_widgets.py            correct — ListView, Badge, IntStepper, etc.
example_advanced_systems.py      correct — pathfinding, lighting, audio
example_phase14.py               WRONG — was renamed to example_ui_widgets.py
example_phase11.py               WRONG — was renamed to example_advanced_systems.py
```

### 5.3 Current Status

All test files are correctly named. No phase-named test files exist.

All example files are correctly named. The phase-named example files
(example_phase11.py, example_phase14.py) have been deleted. Their
replacements (example_advanced_systems.py, example_ui_widgets.py) are
registered in run_examples.py.

### 5.4 Rule for New Files

Before creating a new test or example file:
1. Name it after the system or behaviour it covers
2. Verify the name will still be accurate after the system evolves
3. Ask: "If someone reads only the filename, do they know what this tests?"

If the answer to (3) is no, rename before committing.

---

## 6. The Standards in Summary

**Docstrings:**
- Use for: public contracts — what it is, what it promises, what it needs, what can fail
- Format: Google style. Summary line first. Sections as needed. Short form when simple.
- Frequency: required for every public API in the engine.
- Never: restate type annotations, describe implementation, use past tense,
  write paragraph summary lines, write summaries less informative than the name

**Comments:**
- Use for: implementation decisions — why this approach, why not the alternative,
  why this must not change
- Required: workarounds, invariants, magic numbers, intentional asymmetry,
  defensive notes, algorithm/performance rationale, TODO with full context
- Format: immediately above the code. No blank line between comment and code.
- Never: describe what the code obviously does

**Naming:**
- Test files: test_{module_or_class_name}.py — names the system, not the phase
- Example files: example_{what_it_demonstrates}.py
- Never: phase numbers, dates, "new_", "refactored_" in file or function names

**The tests for your own writing:**
- Docstring: "Does a developer using this API understand the contract
  without reading the implementation?"
- Comment: "Would a developer unfamiliar with this decision benefit
  from this comment?"
- File name: "If someone reads only the filename, do they know what this covers?"

All three should answer yes.
