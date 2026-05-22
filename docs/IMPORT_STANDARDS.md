# pygame_engine — Import Standards

**Version:** 2.0-design
**Authority:** Supplements CODING_STANDARDS.md, Restriction R4

This document defines import ordering, grouping, and patterns.
Consistent imports make diffs cleaner, make the dependency graph
legible, and prevent circular import violations from being introduced
silently.

---

## 1. Import Order — Four Groups

Imports are organised in four groups, separated by blank lines,
in this order:

```python
# Group 1 — Python standard library
from __future__ import annotations
import math
import os
import pathlib
import weakref
from collections.abc import Callable
from typing import TYPE_CHECKING, Generic, TypeVar

# Group 2 — Third-party packages
import pygame

# Group 3 — Engine imports (ordered by dependency layer, low to high)
from pygame_engine.state import Observable, SubscriptionGroup
from pygame_engine.events import EventBus
from pygame_engine.scene import Scene
from pygame_engine.ui import Widget, Panel

# Group 4 — Game imports (only in game code, never in engine code)
from game.ui.desk_theme import DESK_BG, PARCH_BG
from game.ui.desk_button import DeskButton
```

Within each group: alphabetical order by module name.

`from __future__ import annotations` is always first if present.
`TYPE_CHECKING` imports go in a separate block after the normal imports
(see Section 3).

**Enforced by:** `ruff` with `isort` configuration in `pyproject.toml`.

---

## 2. Style Within Groups

**`import X` vs `from X import Y`:**

Use `from X import Y` for specific names you use directly.
Use `import X` when using multiple names from the module and
namespacing adds clarity.

```python
# Specific names — from X import Y
from collections.abc import Callable
from typing import Generic, TypeVar
from pygame_engine.state import Observable

# Namespaced — import X
import pygame           # pygame.Surface, pygame.Rect — namespace is clear
import math             # math.sin, math.cos — namespace avoids ambiguity
import weakref          # weakref.ref — unambiguous with namespace
```

**No star imports:**
```python
# Never
from pygame_engine.state import *
from game.ui.desk_theme import *
```

Star imports make it impossible to know where a name comes from
without reading the source module.

**No aliased imports unless the alias is universally standard:**
```python
# Universally standard aliases — acceptable
import numpy as np        # if numpy is ever added

# Invented aliases — not acceptable
import pygame_engine as pe
from pygame_engine.state import Observable as Obs
```

---

## 3. TYPE_CHECKING Guard

Imports needed only for type annotations — not at runtime — must
be in a `TYPE_CHECKING` block. This prevents circular imports
caused by type hints.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame_engine.scene import Scene
    from editor.panels.inspector import Inspector
```

`from __future__ import annotations` makes all annotations lazy strings
at runtime. The guarded imports are never executed outside of mypy and
the IDE.

**When to use `TYPE_CHECKING`:**
- Any cross-layer import for a type hint only
- Any editor import in engine code
- Any forward reference that would cause a circular import

**When not to use `TYPE_CHECKING`:**
- Imports needed at runtime for `isinstance()` checks
- Imports needed to construct objects or call functions
- Imports in the same layer that are straightforward

---

## 4. Lazy Imports

Lazy imports — imports inside function bodies — are acceptable only
in these specific cases:

**To break circular imports that cannot be resolved with TYPE_CHECKING:**
```python
def push(self, scene) -> None:
    # Lazy import to avoid circular dependency between ui/ and scene/.
    # TODO(restriction=C3): Replace with SceneLike protocol.
    from pygame_engine.scene import Scene
    ...
```

**To defer expensive imports until they are actually needed:**
```python
def start_debug_server(self) -> None:
    # pyimgui is an optional dependency — only import when actually used.
    import imgui
    ...
```

Lazy imports must have a comment explaining why they are lazy.
A lazy import without a comment will be treated as a violation in
code review.

**Lazy imports are not permitted for navigation between game scenes.**
This was acceptable as a transitional pattern but the target state
is the scene registry. See CODEBASE_CHANGES.md C5.

---

## 5. Engine Code Import Constraints

These apply to any file inside `pygame_engine/`:

**Layer 0 modules (Observable, EventBus, TimeManager, etc.) must not
import from Layer 1 or above.** Importing from a higher layer creates
a cycle or violates the dependency direction.

```python
# In pygame_engine/state/observable.py
# Correct — Layer 0 only imports from stdlib and third-party
import weakref
from collections.abc import Callable

# Wrong — Layer 0 importing from Layer 1
from pygame_engine.ui import Widget   # violation: R4
```

**Engine modules (Layer 3) may import from any layer below them,
but game code must not import from engine modules except as an
explicit optional dependency in development-only paths.**

**No engine module imports from `game/`:**
```python
# In pygame_engine/ — never
from game.scenes.management_scene import ManagementScene   # violation: R3
```

---

## 6. Game Code Import Constraints

**Never import from another scene at module level:**
```python
# In game/scenes/inventory_scene.py

# Wrong — module-level cross-scene import
from game.scenes.management_scene import ManagementScene   # violation: R7

# Correct — scene registry
from pygame_engine.scene import get_scene
# ... used inside a method:
scene_class = get_scene("ManagementScene")
```

**Import shared game UI from `game/ui/`, not from scene files:**
```python
# Wrong — importing constants from a scene file
from game.scenes.management_scene import DESK_BG, TAB_H   # violation: R7

# Correct — shared UI module
from game.ui.desk_theme import DESK_BG, TAB_H
```

---

## 7. The Circular Import Diagnostic

When a circular import occurs, Python raises:
```
ImportError: cannot import name 'X' from partially initialized module 'Y'
```

**Diagnose first — do not reach for lazy imports immediately.**

Draw the import graph:
```
A imports B
B imports C
C imports A  ← the cycle
```

**Resolution strategies, in order of preference:**

1. **Extract the shared dependency to a lower layer.** If A and C both
   need something from B, and B needing A causes the cycle, extract
   what A needs into a new module D that neither A nor C imports from.

2. **Use a Protocol (TYPE_CHECKING).** If C only needs A's type, use
   TYPE_CHECKING and a Protocol instead of importing A directly.

3. **Restructure the modules.** Often a cycle means two modules are
   sharing responsibilities they should not.

4. **Lazy import (last resort).** Only if none of the above apply.
   Document why with a TODO linking to CODEBASE_CHANGES.md.

---

## 8. ruff Configuration for Imports

Add to `pyproject.toml`:

```toml
[tool.ruff.lint.isort]
known_first_party = ["pygame_engine", "game"]
force_sort_within_sections = true
lines_between_types = 1

[tool.ruff.lint]
select = [
    "I",    # isort — import ordering
    "F401", # unused imports
    "F811", # redefined unused name
]
```

Running `ruff check --fix .` automatically fixes import ordering.
Run this before every commit.

---

## 9. Game Code Dependency Direction

Within the game layer (`game/`), imports follow the same principle as
the engine layer — lower-level modules have no knowledge of higher-level
ones. This prevents the same class of coupling problems that the engine
restrictions address.

### Game Layer Dependency Direction

```
scenes/       may import from: game/ui/, systems/, core/
systems/      may import from: core/, models/
models/       may import from: core/
core/         may import from: nothing in game/
game/ui/      may import from: nothing in game/ (pure constants and widgets)
```

Visualised:

```
game/ui/   core/
    ↑        ↑
  models/    |
      ↑      |
  systems/ ──┘
      ↑
  scenes/
```

Arrows mean "may import from." Lower modules have no knowledge of
higher modules.

### What This Prevents

**systems/ importing from scenes/**
A system that imports from a scene is a system coupled to a specific
screen layout. If the scene is restructured, the system breaks.
Systems must be scene-agnostic.

**scenes/ importing from other scenes/**
Already covered by Restriction R7 and Section 6 above. Repeated here
for completeness — it applies in the game dependency direction too.

**game/ui/ importing from systems/ or scenes/**
The desk theme constants and `DeskButton` must be usable by any scene
without pulling in game logic. If `desk_theme.py` imported from
`systems/`, every scene that uses a colour constant would transitively
depend on the entire systems layer.

### Violations Currently in the Codebase

The import of palette constants from `management_scene.py` into other
scenes violates this direction. The fix is tracked as CODEBASE_CHANGES.md
C2 — move constants to `game/ui/desk_theme.py`.

Once C2 is resolved, the game layer dependency direction will be clean.
