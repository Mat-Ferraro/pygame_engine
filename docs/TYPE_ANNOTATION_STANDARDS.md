# pygame_engine — Type Annotation Standards

**Version:** 2.0-design
**Authority:** Supplements CODING_STANDARDS.md

This document defines when to annotate, what to annotate, and how to
annotate in pygame_engine and all projects built with it.

The goal is "moderate but intentional typing" — enough annotation that
IDEs give useful autocomplete and mypy catches real bugs, not so much
that annotations obscure the code they describe.

---

## 1. The Rule Set

### Always Annotate

**All public method signatures — parameters and return type:**
```python
def subscribe(self, callback: Callable[[T, T], None]) -> Token:
def set(self, value: T) -> None:
def load(self, path: str) -> dict:
```

`-> None` on public methods is always explicit. Omitting it is ambiguous
— does this return nothing or did the developer forget to annotate?

**All class-level attributes declared in `__init__`:**
```python
def __init__(self) -> None:
    self._subscribers: list[weakref.ref] = []
    self._value:       T
    self._disposed:    bool = False
```

**Any local variable whose type is not immediately obvious:**
```python
# Annotate — not obvious from context
mapping: dict[str, type[Scene]] = {}
handlers: list[Callable[[pygame.event.Event], bool]] = []

# Do not annotate — obvious from assignment
result  = font.size(text)      # tuple[int, int]
surface = pygame.Surface((w, h))
```

### Never Annotate

**Loop variables when the iterable is typed:**
```python
# The iterable is typed — loop var type is inferred
for child in self._children:       # _children: list[Widget]
    child.render(surface)

# Annotate only if the inferred type is wrong or misleading
for item in mixed_list:            # list[Widget | Panel]
    widget: Widget = item          # clarifies intended usage
```

**Simple tuple unpacking where the source is typed:**
```python
width, height = surface.get_size()   # obvious — get_size() -> tuple[int, int]
```

**Return type when the function is a generator** — use `Iterator[T]` or
`Generator[T, None, None]` instead of a bare annotation.

---

## 2. The TYPE_CHECKING Guard

Any import needed only for type annotations — not at runtime — must be
guarded with `TYPE_CHECKING`. This prevents circular imports introduced
purely by type hints.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.scene import Scene
    from editor.panels.inspector import Inspector
```

`from __future__ import annotations` makes all annotations strings at
runtime, so the guarded import is never executed outside type checking.

**When to use it:**
- Any cross-layer import needed only for a type hint
- Any editor import in engine code
- Any forward reference that would otherwise cause an import cycle

**When not to use it:**
- Imports needed at runtime for isinstance() checks
- Imports needed to construct objects

---

## 3. Generic Types

Use Python's built-in generic syntax from Python 3.9+ where possible.
Do not use `typing.List`, `typing.Dict`, `typing.Tuple` — these are
deprecated.

```python
# Correct — built-in generics
def get_children(self) -> list[Widget]:
def get_registry(self) -> dict[str, type[Scene]]:
def get_size(self) -> tuple[int, int]:

# Wrong — deprecated typing aliases
from typing import List, Dict, Tuple
def get_children(self) -> List[Widget]:
```

For `Optional`, use `X | None` syntax:
```python
# Correct
def get_focused(self) -> Widget | None:
def find(self, widget_id: str) -> WidgetNode | None:

# Wrong — verbose, deprecated
from typing import Optional
def get_focused(self) -> Optional[Widget]:
```

For `Union`, use `X | Y` syntax:
```python
colour: tuple[int, int, int] | tuple[int, int, int, int]
```

---

## 4. Callable Annotations

Callbacks are the most common annotation challenge. Use `Callable` from
`collections.abc` (not `typing.Callable` — it is the same but the
`collections.abc` version is preferred from 3.9+).

```python
from collections.abc import Callable

# Correct annotation forms
on_change:  Callable[[T, T], None]           # subscriber: (old, new) -> None
on_click:   Callable[[], None]               # no arguments
predicate:  Callable[[Widget], bool]         # filter function
factory:    Callable[[], Scene]              # scene factory
```

When a callback has many parameters, define a `Protocol` instead:

```python
from typing import Protocol

class SceneFactory(Protocol):
    def __call__(self, app: Application, state: dict) -> Scene: ...
```

---

## 5. TypeVar and Generic Classes

`Observable[T]` is generic. Defining generic classes uses `TypeVar`:

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Observable(Generic[T]):
    def __init__(self, initial: T) -> None:
        self._value: T = initial

    def set(self, value: T) -> None: ...
    @property
    def value(self) -> T: ...
```

`TypeVar` names follow the convention: single capital letter `T`, `K`, `V`
for simple cases; descriptive names for constrained types:

```python
SceneT  = TypeVar("SceneT", bound=Scene)
WidgetT = TypeVar("WidgetT", bound=Widget)
```

---

## 6. pygame-ce Type Stubs

pygame-ce ships with partial type stubs. Some types need explicit
annotation because the stubs are incomplete or incorrect.

**Always annotate these explicitly:**
```python
surface: pygame.Surface
rect:    pygame.Rect
font:    pygame.font.Font
colour:  tuple[int, int, int] | tuple[int, int, int, int]
event:   pygame.event.Event
```

**Known stub gaps** — annotate these manually:
```python
# pygame.Surface.get_size() — stubs may not reflect the correct return type
size: tuple[int, int] = surface.get_size()

# pygame.font.Font.size() — returns tuple[int, int]
width, height = font.size(text)  # type: tuple[int, int]
```

---

## 7. Enforced vs Not Enforced

**Enforced by mypy in CI for `pygame_engine/` public modules:**
- All public method signatures annotated
- No untyped function definitions in public modules (`--disallow-untyped-defs`)
- No implicit `Any` in public signatures

**Not enforced (honour system):**
- Private method annotations
- Game code in `game/`
- Test files

**Mypy configuration in `pyproject.toml`:**
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = "pygame_engine.*"
disallow_untyped_defs = true
disallow_incomplete_defs = true

[[tool.mypy.overrides]]
module = ["pygame.*", "imgui.*"]
ignore_missing_imports = true
```

---

## 8. Common Patterns in This Codebase

**Colour type:**
```python
# Use a type alias for clarity
Colour = tuple[int, int, int] | tuple[int, int, int, int]

def draw_rect(surface: pygame.Surface, rect: pygame.Rect, colour: Colour) -> None:
```

**Callback token:**
```python
class Token:
    """Represents a subscription that can be cancelled."""
    def cancel(self) -> None: ...

# Returned by Observable.subscribe() and EventBus.on()
def subscribe(self, callback: Callable[[T, T], None]) -> Token:
```

**Widget or None pattern:**
```python
# Use | None, not Optional
def find_widget(self, widget_id: str) -> Widget | None:
    return self._registry.get(widget_id)
```

**Literal types for constrained strings:**
```python
from typing import Literal

Mode     = Literal["development", "production", "testing"]
Direction= Literal["left", "right", "up", "down"]
BusName  = Literal["master", "music", "sfx", "ui"]

def __init__(self, mode: Mode = "development") -> None:
```

---

## 9. What to Do When You're Unsure

If you are unsure whether to annotate something or how, apply this test:

**Would the wrong type here cause a bug that mypy would catch?**

If yes — annotate. The annotation prevents a real class of error.
If no — use your judgement. Annotation is optional.

When a type is genuinely complex and the annotation would be longer than
the code itself, use a type alias with a clear name rather than an
inline annotation:

```python
# Complex inline — hard to read
handlers: dict[str, list[weakref.ref[Callable[[pygame.event.Event], bool]]]] = {}

# Type alias — readable
EventHandler = Callable[[pygame.event.Event], bool]
HandlerMap   = dict[str, list[weakref.ref[EventHandler]]]

handlers: HandlerMap = {}
```

---

## 10. __init__ and Special Methods

**`__init__` always annotates `-> None`:**
```python
def __init__(self, value: T, initial: int = 0) -> None:
```

This is required by `--disallow-untyped-defs` and makes the rule
consistent. `__init__` never returns a value — annotating `-> None`
makes that explicit rather than relying on mypy's inference.

**`__repr__` always returns `str`:**
```python
def __repr__(self) -> str:
    return f"Observable({self._value!r})"
```

**`__eq__` and `__hash__` — annotate when overriding:**
```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Observable):
        return NotImplemented
    return self._value == other._value

def __hash__(self) -> int:
    return hash(self._value)
```

Note: `other: object` not `other: Observable` — this is the correct
signature for `__eq__`. mypy enforces it.

---

## 11. Overloaded Methods

When a method accepts meaningfully different argument shapes and returns
different types depending on the shape, use `@overload`:

```python
from typing import overload

class AssetManager:

    @overload
    def load(self, path: str) -> pygame.Surface: ...

    @overload
    def load(self, path: str, *, as_sound: Literal[True]) -> pygame.mixer.Sound: ...

    def load(
        self,
        path: str,
        *,
        as_sound: bool = False,
    ) -> pygame.Surface | pygame.mixer.Sound:
        """Load an asset from path."""
        if as_sound:
            return pygame.mixer.Sound(path)
        return pygame.image.load(path)
```

Rules for `@overload`:
- Overload signatures have `...` as the body — never implementation code
- The implementation signature is not decorated with `@overload`
- The implementation signature uses `Union` (or `|`) to cover all cases
- The docstring goes on the implementation, not on the overloads
- Only use `@overload` when the return type genuinely differs — not just
  for documentation of parameter options

---

## 12. Type Aliases — When and How

Use type aliases when the same complex type appears in multiple places
or when giving a name to the type adds meaning.

**When to create an alias:**
```python
# Complex type used in multiple places
Colour = tuple[int, int, int] | tuple[int, int, int, int]

# Type whose name adds domain meaning
WidgetId = str                    # distinguishes from arbitrary str
EventName = str                   # distinguishes from arbitrary str
SchemaVersion = int               # distinguishes from arbitrary int
```

**When not to create an alias:**
```python
# Simple type used once — no alias needed
def get_title(self) -> str: ...

# Generic type that mypy infers correctly — no alias needed
children: list[Widget] = []
```

**Where to define aliases:**
- Module-level in the file where they are first used
- In a `types.py` module if used across multiple files in the same package
- Never in `__init__.py` — type aliases belong in the module that owns them

**Naming:**
- `PascalCase` for type aliases (they name a type concept)
- Descriptive enough to add meaning over the underlying type
- `Colour` not `ColourTuple` — the word "tuple" is implementation detail
- `WidgetId` not `WidgetIdStr` — the "str" is implementation detail
