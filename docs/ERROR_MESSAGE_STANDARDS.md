# pygame_engine — Error Message Standards

**Version:** 2.0-design
**Authority:** Supplements ARCHITECTURE.md Section 3.12

Every error message is a message to a developer who is stuck. The
quality of that message directly affects how long they stay stuck.
A good error message is one of the highest-leverage things we write.

---

## 1. The Three Questions

Every error message must answer:

1. **What went wrong** — factual, specific, includes the bad value
2. **What was expected** — what would have been correct
3. **What to do** — concrete next step or reference

If the message does not answer all three, it is incomplete.

```python
# Bad — answers none of the three
raise EngineError("Invalid widget")

# Bad — answers only (1)
raise EngineError(f"widget_id '{widget_id}' not found")

# Good — answers all three
raise EngineError(
    f"widget_id '{widget_id}' not found in the scene descriptor registry.\n"
    f"Expected: a widget_id registered via Widget.__init__(widget_id='...').\n"
    f"Registered ids: {sorted(self._registry.keys()) or ['none yet']}.\n"
    f"Ensure _build_layout() has been called before accessing the registry."
)
```

---

## 2. The Three Error Categories

These are defined in ARCHITECTURE.md Section 3.12. Message style
follows from the category.

### Developer Errors

Wrong API usage — wrong types, invalid arguments, calling methods
in the wrong order. These are bugs in the developer's code.

**Message style:** Direct, specific, tells the developer exactly
what they did wrong and what to do instead.

```python
# Wrong type
if not isinstance(scene, Scene):
    raise EngineError(
        f"SceneManager.push() expected a Scene instance, "
        f"got {type(scene).__name__}.\n"
        f"Did you pass the class instead of an instance? "
        f"Use push(MyScene(app)) not push(MyScene)."
    )

# Wrong order
if not self._running:
    raise EngineError(
        f"Cannot access {property_name!r} before Application.run() "
        f"has been called. Move this access into on_enter() or later."
    )

# Invalid value
if not 0.0 <= volume <= 1.0:
    raise EngineError(
        f"AudioBus.volume must be in range 0.0–1.0, got {volume}.\n"
        f"Values outside this range have no additional effect."
    )
```

### Asset Errors

Missing files, corrupt data, format mismatches. These can happen in
production and must not crash the game.

**Message style:** Factual and specific, but the message is logged
— not raised. The engine substitutes a placeholder and continues.

```python
debug_log.error(
    f"Asset not found: {path}\n"
    f"A placeholder will be used. Check that the path is relative to "
    f"the project root and the file exists.",
    tag="asset_manager"
)
```

If the asset failure is critical and no placeholder is possible:
```python
raise AssetError(
    f"Required asset not found: {path}\n"
    f"This asset has no placeholder — the game cannot continue without it.\n"
    f"Check that the file exists and the project layout matches "
    f"the expected structure (see docs/how_to/distribute_your_game.md)."
)
```

### Runtime Errors

Scene throws during update or render. Caught by the engine.
These are logged and displayed through the ErrorScene.

The error message the developer sees comes from the original exception.
The engine wraps it with context:

```python
# Engine-added context — not written by the game developer
context = (
    f"Unhandled exception in {scene.__class__.__name__}.{method_name}().\n"
    f"The scene has been stopped. The error scene is now active.\n"
    f"Original error: {type(exception).__name__}: {exception}"
)
```

---

## 3. Formatting Rules

**Use f-strings, not concatenation:**
```python
# Correct
raise EngineError(f"Expected {expected!r}, got {actual!r}.")

# Wrong
raise EngineError("Expected " + repr(expected) + ", got " + repr(actual) + ".")
```

**Use `!r` for values that could be None, empty, or misleading:**
```python
# Without !r — "None" could be the string "None" or the value None
f"widget_id {widget_id} not found"

# With !r — unambiguous
f"widget_id {widget_id!r} not found"
```

**Multi-line messages use `\n` for line breaks:**
```python
raise EngineError(
    f"Scene stack depth limit ({self._max_depth}) exceeded.\n"
    f"Current stack: {[s.__class__.__name__ for s in self._stack]}.\n"
    f"This usually means a scene is pushing scenes in a loop. "
    f"Check on_enter() for accidental recursive scene pushes."
)
```

**Include the valid range or valid values when relevant:**
```python
raise EngineError(
    f"Unknown transition direction {direction!r}.\n"
    f"Valid directions: 'left', 'right', 'up', 'down'."
)

raise EngineError(
    f"Scene stack depth ({depth}) exceeds limit ({MAX_STACK_DEPTH}).\n"
    f"Configure the limit via AppConfig.max_scene_stack_depth."
)
```

---

## 4. What Not to Write

**No apology:**
```python
# Wrong — an apology adds no information
raise EngineError("Sorry, the widget was not found.")

# Correct
raise EngineError(f"Widget '{widget_id}' not found in registry.")
```

**No vague wording:**
```python
# Wrong — what "invalid" means is unspecified
raise EngineError("Invalid argument.")

# Correct
raise EngineError(
    f"tab_index must be a non-negative integer or None, got {tab_index!r}."
)
```

**No implementation details:**
```python
# Wrong — the developer does not care about our internal dict
raise EngineError(
    f"Key '{key}' missing from self._registry dict."
)

# Correct
raise EngineError(
    f"widget_id '{key}' not registered. "
    f"Call Widget.__init__(widget_id='{key}') before accessing it."
)
```

**No stack trace in the message** — Python adds the stack trace
automatically. Repeating it in the message duplicates output.

**No markdown in the message** — error messages appear in terminals
and the error scene. Markdown syntax (`**bold**`, `\`code\``) is
rendered as literal characters.

---

## 5. Exception Types

**`EngineError`** — base class for all engine-raised errors.
Use this when no more specific type applies.

**`AssetError(EngineError)`** — asset loading failures.

**`SceneStackError(EngineError)`** — scene stack violations
(stack overflow, pop from empty stack).

**`LayoutError(EngineError)`** — layout file format errors,
descriptor inconsistencies.

**`ConfigError(EngineError)`** — invalid AppConfig values.

Do not use Python builtins (`ValueError`, `TypeError`, `KeyError`)
for engine-level errors — they give no context about which engine
system raised them. Use a specific `EngineError` subclass.

The one exception: `TypeError` from the standard library is acceptable
for obviously wrong types where the Python error message is already clear.

---

## 6. Error Messages in Game Code

Game code does not use `EngineError` — that is an engine type.
Game code raises Python builtins or game-defined exception types.

The same three-question rule applies to all error messages regardless
of source. A game developer who writes:

```python
raise ValueError("Invalid hero")
```

is leaving future-them and their collaborators to guess what was invalid
and how to fix it. The correct form:

```python
raise ValueError(
    f"Hero {hero.name!r} cannot be assigned to task {task.id!r}.\n"
    f"Reason: hero is already on task {hero.current_task_id!r}.\n"
    f"Unassign the hero first via task_dispatch.unassign_hero()."
)
```

---

## 7. Logging vs Raising

**Raise when:** the operation cannot complete and continuing would
produce incorrect results. The caller must know something went wrong.

**Log and continue when:** something unexpected happened but the
operation can complete with a reasonable fallback. The developer
should know but the game should not crash.

```python
# Raise — cannot complete without the asset
font = app.assets.load_font("assets/fonts/main.ttf", size=22)
if font is None:
    raise AssetError(
        "Required font 'assets/fonts/main.ttf' could not be loaded.\n"
        "This font is used for all UI text — the game cannot run without it."
    )

# Log — can complete with a fallback
font = app.assets.load_font("assets/fonts/optional.ttf", size=22)
if font is None:
    debug_log.warn(
        "Optional font 'assets/fonts/optional.ttf' not found. "
        "Using system font fallback.",
        tag="asset_manager"
    )
    font = pygame.font.SysFont(None, 22)
```

---

## 8. Error Messages in the Editor

The editor has an additional display surface — the inspector panel
and the error panel. Error messages that appear in the editor must
be:

- Short enough to read in a panel (~80 characters per line)
- Specific enough to act on without switching to the terminal
- Include the widget_id or node_id if the error is widget-specific

```python
# Good for editor display — short, specific, actionable
f"Cannot move '{node.widget_id}': it is editor-locked.\n"
f"Unlock it in the hierarchy panel first."

# Bad for editor display — too long, contains internal detail
f"The widget node object at memory address 0x7f... with id "
f"'{node.widget_id}' cannot be moved because its editor_locked "
f"attribute is set to True in the SceneDescriptor..."
```

---

## 9. Warning Messages

Warnings differ from errors — they communicate unexpected but handled
conditions, deprecations, and approaching-limit situations. They do
not stop execution.

### Format — Two Questions

Warning messages answer two questions:
1. What condition warrants the warning
2. What the developer should do if they care

```python
# Good — states the condition and the action
debug_log.warn(
    f"Scene stack depth {depth}/{self._max_depth}. "
    f"Approaching the configured limit. "
    f"If intentional, raise AppConfig.max_scene_stack_depth.",
    tag="scene_manager"
)

# Bad — states only the condition
debug_log.warn("Scene stack depth high.", tag="scene_manager")
```

### Deprecation Warnings

Use Python's `warnings` module for deprecated public API. This gives
developers the file and line number of their own code that uses the
deprecated API — far more useful than a log message.

```python
import warnings

def subscribe_single_arg(self, callback: Callable[[T], None]) -> Token:
    warnings.warn(
        "Observable.subscribe() with a single-argument callback is deprecated. "
        "Use callback(old_value, new_value) instead. "
        "Single-argument callbacks will raise in version 2.0.",
        DeprecationWarning,
        stacklevel=2,   # points to the caller's line, not this line
    )
```

`stacklevel=2` is almost always correct — it makes the warning point to
the caller's code rather than to the deprecation shim. Without it, the
warning points to this file, which is useless.

### Approaching-Limit Warnings

When a system has a configurable limit, warn before the limit is hit —
not after. "You have reached the limit" is too late. "You are approaching
the limit" gives the developer time to act.

```python
# Warn at 80% of the limit — gives headroom to act
if len(self._stack) >= int(self._max_depth * 0.8):
    debug_log.warn(
        f"Scene stack at {len(self._stack)}/{self._max_depth} scenes. "
        f"Approaching the configured maximum. "
        f"Check for scenes being pushed in loops.",
        tag="scene_manager"
    )
```

### Development-Only Warnings

Some warnings are only useful during development and would confuse
players if shown in production. Gate them on `app.mode`:

```python
if app.mode == "development":
    debug_log.warn(
        f"Widget '{self.widget_id}' rendered without a widget_id set. "
        f"Set widget_id in __init__() to enable editor support.",
        tag="editor"
    )
```
