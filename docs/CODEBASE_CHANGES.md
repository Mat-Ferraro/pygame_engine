Changes are ordered: highest priority (blocks new features) first.

---

## Priority 1 -- Must Change Before New Features

### C1 — Theme Singleton Must Move to Application

**What:** `get_theme()` returns a module-level singleton shared across
all `Application` instances in the same process. Two `Application`
instances — which occur in tests and when the editor runs alongside the
game — share theme state. One instance's `set_theme()` call changes the
theme for the other.

**Where:** `pygame_engine/theme/runtime.py` and every widget that calls
`get_theme()` — approximately 42 call sites across `ui/`, `dialogue/`,
and `theme/`.

**Why:** Module-level singletons violate Restriction R9 and make the
engine untestable in isolation. (Restriction R9)

**Required changes:**
1. `Application` gains a `theme: Observable[Theme]` property
2. `set_theme()` and `get_theme()` on `Application` replace module-level functions
3. Widgets receive theme through `render(surface, theme)` parameter —
   breaking change to Widget interface, correct pre-1.0
4. Module-level `get_theme()` becomes a deprecated wrapper

**Restriction:** R9 (No stateful singletons)

---

### C8 — Observable[T] Upgrade ✅ RESOLVED (CHANGE-01 + CHANGE-07)

**What:** Current `Observable[T]` lacks weak reference subscriptions,
transaction batching, and old-value in event payload.

**Why:** These are correctness features. Memory leaks from forgotten
unsubscription. Event storms when multiple properties change. Undo
commands cannot be implemented without old/new value pairs. Everything
in Phase 2+ depends on this being correct.

**Required changes:**
1. Subscriptions use `weakref.ref` — dead refs cleaned up lazily
2. `Observable.transaction()` context manager fires one event on exit
3. Subscriber signature changes to `callback(old_value, new_value)`
4. New `SubscriptionGroup` with `add()`, `on()`, `dispose()`
5. Wire `SubscriptionGroup` into `Scene.on_exit()` for auto cleanup
6. Full test suite before anything builds on top:
   - Property-based tests via Hypothesis
   - Weak ref cleanup, circular event prevention, transaction batching,
     old-value correctness, scale benchmark

**Resolved:** weak refs, transaction(), (old, new) signature, SubscriptionGroup,
Scene.subscriptions auto-cleanup — all implemented and tested.

**Restriction:** Foundation for all Phase 1+ work

---


### C2 -- Shared Game UI Must Leave management_scene.py

What: All game scenes import palette constants and DeskButton from
management_scene.py, making a scene file into a shared library.

Where: inventory_scene.py, market_scene.py, rival_guilds_scene.py,
legacy_scene.py, training_scene.py, guild_upgrades_scene.py,
campaign_map_scene.py -- all importing from management_scene.py.

Why: A scene file is a leaf in the dependency graph. Making it a shared
library means changes to it can break unrelated scenes.
(Restrictions R4, R7)

Required changes:
Create game/ui/desk_theme.py -- all palette and layout constants.
Create game/ui/desk_button.py -- DeskButton class.
Update all scene imports to reference game/ui/ instead.
The constants and class do not change -- only their location.

Restriction: R4 (Dependency direction), R7 (Scenes do not import each other)

---

### C3 -- ConfirmDialog Circular Import Workaround

What: ConfirmDialog uses a lazy _Adapter(Scene) inside push() to avoid
a circular import between pygame_engine/ui/ and pygame_engine/scene/.

Where: pygame_engine/ui/feedback/confirm_dialog.py

Why: The workaround is a symptom of a structural problem. Should be
resolved with a protocol, not a runtime hack. (Restriction R2)

Required changes:
Audit the import chain. Likely solution: ConfirmDialog uses a SceneLike
protocol instead of importing Scene directly. The protocol lives at Layer 0
with no engine imports. Both Scene and ConfirmDialog reference the protocol.

Restriction: R2 (No circular dependencies)

---

## Priority 2 -- Should Change Before Building Editor

---

### C4 -- management_scene.py Decomposition

What: management_scene.py is ~937 lines -- exceeds 600-line hard cap.
No new features can be added until decomposed.

Required decomposition:
  game/scenes/management/
    __init__.py              # re-exports ManagementScene
    management_scene.py      # scene orchestrator (~200L)
    recruit_list.py          # recruit list rendering (~200L)
    roster_list.py           # roster list rendering (~150L)
    detail_panel.py          # hero detail panel (~200L)
    negotiation_panel.py     # negotiation controls (~150L)

Restriction: R17 (File length limits)

---

### C5 -- Scene Navigation Must Use Registry

What: TabBar._navigate() uses lazy imports of scene classes.
These create scene-to-scene dependencies even as lazy imports.

Required changes:
1. Implement @register_scene decorator and scene registry.
2. Add @register_scene to all game scene classes.
3. Update TabBar._navigate() to use get_scene(ClassName).
4. Remove all lazy scene class imports from navigation code.

Restriction: R7 (Scenes do not import each other)

---

### C6 -- game_hub_scene.py Decomposition

What: ~619 lines -- exceeds 600-line hard cap.

Required decomposition:
  game/scenes/hub/
    __init__.py
    game_hub_scene.py    # orchestrator (~150L)
    roster_panel.py      # hero roster snapshot (~150L)
    notice_panel.py      # notice board (~150L)
    world_panel.py       # campaign and world state (~150L)

Restriction: R17

---

### C7 -- inventory_scene.py Decomposition

What: ~600 lines -- at hard cap.

Required decomposition:
  game/scenes/inventory/
    __init__.py
    inventory_scene.py   # orchestrator (~150L)
    item_list.py         # guild inventory panel (~150L)
    hero_list.py         # hero roster panel (~100L)
    loadout_panel.py     # equipped items panel (~100L)
    detail_panel.py      # item and hero detail (~100L)

Restriction: R17

---

## Priority 3 -- Cleanup

---

### C9 -- Abbreviations in Game Render Methods

What: sw/sh, col (ambiguous), lx/rx, by/bx throughout game scene files.

Where: All game scenes in render() and _draw_*() methods.

Most problematic: col used as both colour and column position in the
same file. This is direct cognitive overhead.

Changes:
  sw -> surface.get_width() or surface_width
  sh -> surface.get_height() or surface_height
  col (colour) -> colour
  col (column position) -> column_x or col_x
  lx -> left_x, rx -> right_x
  by -> button_y, bx -> button_x

Restriction: R16 (Naming conventions)

---

### C10 -- Docstring Coverage

What: Phase 14 widgets have class docstrings but minimal method docstrings.

Priority order:
1. Observable[T] -- all public methods with postcondition docs
2. Widget -- handle_event, update, render, set_rect
3. Phase 14 widgets -- render, handle_event, primary action method
4. SceneManager -- push, pop, replace, push_with

Reference: text_utils.py is a good template for complete docstrings.

Restriction: R15 (Every public API has a docstring)

---

### C11 -- Game Scene Smoke Tests

What: All game scenes have zero test coverage.

Note: Cannot be written until SceneTestHarness exists (Phase 4).
Track as follow-up to Phase 4 completion.

Basic test pattern:
  def test_management_scene_loads():
      harness = SceneTestHarness()
      harness.load(ManagementScene, context=ManagementScene.editor_context())
      harness.advance(dt=0.016)
      # No exception = pass

Restriction: R11 (No feature without a test, game scene tier)

---

### C12 -- EventBus Singleton -- Formal Exception to R9

What: The module-level bus singleton in pygame_engine/events/ is an
intentional exception to the no-singletons restriction.

Action: Add a comment to pygame_engine/events/__init__.py documenting
this as an explicit, reasoned exception to R9:
  - Predates the restriction
  - Used for truly cross-cutting concerns
  - Editor and game subscriptions are independent on a shared bus
  - Less severe isolation issue than the theme singleton

No code change required.

---

### C13 -- Soft-Limit Scenes

What: rival_guilds_scene.py (~450L), legacy_scene.py (~450L),
market_scene.py (~500L) are over the 400-line soft limit.

Action: Review for decomposition when new features are added to these
files. Not urgent -- soft limit, not hard cap.

Restriction: R17

---

## Change Summary

| ID  | Change                            | Priority | Restriction | Blocks           |
|-----|-----------------------------------|----------|-------------|------------------|
| C1  | Theme singleton -> Application    | 1        | R9          | Editor, tests    |
| C2  | Shared UI out of management_scene | 1        | R4, R7      | C4               |
| C3  | ConfirmDialog circular import     | 1        | R2          | Editor           |
| C8  | Observable upgrade                | 1*       | --          | Editor, all      |
| C4  | management_scene decomposition    | 2        | R17         | New features     |
| C5  | Navigation via scene registry     | 2        | R7          | Editor discovery |
| C6  | game_hub_scene decomposition      | 2        | R17         | New features     |
| C7  | inventory_scene decomposition     | 2        | R17         | New features     |
| C9  | Abbreviation cleanup              | 3        | R16         | Nothing          |
| C10 | Docstring coverage                | 3        | R15         | Nothing          |
| C11 | Game scene smoke tests            | 3        | R11         | Needs Phase 4    |
| C12 | EventBus singleton exception      | 3        | R9          | Nothing (docs)   |
| C13 | Soft-limit scenes                 | 3        | R17         | Nothing          |

* C8 is Priority 1 in importance but logically belongs with all
  infrastructure changes. It is the foundation for C1.

## Sequencing Notes

Do in this order:
1. C8 (Observable upgrade) -- foundation for everything else
2. C1 (Theme singleton) -- uses Observable for reactivity
3. C2, C3 (Game UI extraction, ConfirmDialog) -- independent, can be parallel
4. C4, C5, C6, C7 (Decomposition and registry) -- when editor build begins
5. C9, C10, C11, C12, C13 -- ongoing cleanup, no ordering dependency