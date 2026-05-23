# Sprint — Scene Descriptor as Source of Truth (F3 completion)

**Status:** Complete
**Owner:** _(you)_
**Phase context:** Phase F — Scene Editor. Closed the F3 gap; unblocks F4–F6.

---

---

## 1. Background — why this sprint exists

The Scene Editor roadmap (Phase F) lists F3 — "Viewport rendering — scene
visible in editor window" — as *Partial*. Investigation showed the gap is
deeper than a rendering bug.

The engine currently contains **two parallel, unreconciled models of a
scene's UI**:

- **Live widget tree.** Real scenes (`MainMenuScene`, `GameScene`, …) are
  plain `Scene` subclasses. They build widgets directly in code with raw
  `pygame.Rect` geometry. This is what actually renders.
- **`SceneDescriptor`.** A separate observable tree of `WidgetNode`s, built
  via `DescribedScene` + the `layout_builder` DSL. This is what the editor's
  hierarchy and inspector read. Almost no real scene uses it.

The editor therefore *inspects* one model and *renders* a different one,
with nothing connecting them. `DescribedScene`'s docstring claims "live
two-way binding" — no code delivers it. `layout_builder`, the prefab fields
on `WidgetNode`, and `.layout.json` persistence are all built but unused.

This is the redundancy the project's standards explicitly forbid: two
systems doing one job, half-built.

## 2. The decision (to be promoted to `accepted_decisions.md` on sprint close)

> **The `SceneDescriptor` is the single source of truth for a scene's UI
> layout.** Scenes declare their UI structure and geometry by populating a
> descriptor. The engine instantiates the real widget tree *from* the
> descriptor. The editor edits the descriptor; the live widgets follow.

Rejected alternative: making the live widget tree authoritative and treating
the descriptor as a derived view. That path turns `DescribedScene`, the
`layout_builder` DSL, the prefab fields, and `.layout.json` into permanent
dead code, and a scene that rebuilds widgets from code each `on_enter()`
would silently overwrite any saved layout. It also reduces the "editor" to
an inspector that cannot author.

**Consequence:** real scenes migrate to `DescribedScene`. This sprint
migrates one (`MainMenuScene`) as the proving ground; the rest follow in
later, separate work.

### 2.1 Layout / behaviour split

The descriptor describes **structure and geometry only**. It must stay
JSON-serialisable, so it cannot hold callables.

- **Layout data** (type, rect, static props like label text) → the
  descriptor.
- **Behaviour** (`on_click` handlers, navigation, game wiring) → attached by
  the scene *after* the widget tree is built, by looking widgets up via
  `widget_id`.

### 2.2 Layout helpers (`anchor` / `column` / `flex`)

For this sprint: helpers are **computed inside `_build_layout()`** and their
*results* (literal `x/y/w/h` numbers) are stored in the descriptor. The
descriptor stays a flat data model.

Storing an unresolved anchor spec in the descriptor — so layouts re-flow on
window resize — is a real future capability but is **out of scope** here.
See Open Questions.

## 3. Scope

**In scope:**

1. `pygame_engine/ui/widget_registry.py` — new. Maps `WidgetNode.type`
   strings to builder functions. Single source of truth for which widget
   types exist and how each is constructed from `(rect, props)`. Built-in
   types self-register; games may register custom types.
2. `pygame_engine/scene/layout_loader.py` — new. `LayoutLoader`: walks a
   `SceneDescriptor`, uses the registry to instantiate the real widget tree,
   returns the root widget. Subscribes each widget's rect to its
   `node.rect` so descriptor edits move live widgets — the real F3.
3. `pygame_engine/scene/described_scene.py` — rewrite. After
   `_build_layout()` populates the descriptor, `on_enter()` builds the
   widget tree via the loader and exposes it as `root_widget`. New
   `_bind_behavior()` hook for scenes to attach callbacks by `widget_id`.
4. Migrate `MainMenuScene` to `DescribedScene` — the proving scene.
5. Promote the Section 2 decision into `docs/accepted_decisions.md`.

**Explicitly out of scope:**

- F4 (selection gizmo), F5 (inspector editing), F6 (play/stop polish) —
  each its own later pass, now sitting on a sound F3.
- Migrating `GameScene`, `SettingsScene`, `PauseScene` — later work.
- Anchor-spec persistence / responsive descriptor layout (see 2.2).
- Advanced 2D lighting (L0–L5) — stretch goal, not scheduled, unaffected.

## 4. Build order

Each step is independently reviewable; do not start the next until the
current one compiles and reads cleanly.

| # | Deliverable | Done when |
|---|---|---|
| 1 | `widget_registry.py` | Built-in types register; lookup + build by type string works; unknown type raises a clear error |
| 2 | `layout_loader.py` | Descriptor → widget tree; rect binding wired; handles nested containers |
| 3 | `described_scene.py` rewrite | `on_enter()` builds `root_widget` from descriptor; `_bind_behavior()` hook present |
| 4 | `MainMenuScene` migration | Menu renders and its buttons work, driven entirely by the descriptor |
| 5 | Decision recorded | Entry added to `accepted_decisions.md` |

## 5. Definition of done

- A `DescribedScene` opened in the editor renders from its descriptor, and
  editing a `node.rect` visibly moves the live widget.
- `MainMenuScene` is a `DescribedScene`: structure in `_build_layout()`,
  behaviour in `_bind_behavior()`, and it runs identically to before.
- No `if type == "Button"`-style branching in the loader — all type
  knowledge lives in the registry.
- The descriptor remains JSON-serialisable (no callables stored).
- The decision is written into `accepted_decisions.md`.

## 6. Open questions / deferred

1. **Anchor-spec persistence.** Should the descriptor eventually store an
   unresolved layout spec (anchor/column/flex) so layouts re-flow on resize?
   `layout_builder` already hints at this with `L.dynamic()`. Deferred — a
   later design effort, not this sprint.
2. **Custom widget-type registration ergonomics.** Games will register their
   own widget types with the registry. The exact registration API (decorator
   vs explicit call) is settled in step 1; revisit if it proves awkward
   during a real game's migration.
3. **Behaviour-binding lookup misses.** When `_bind_behavior()` references a
   `widget_id` not in the tree (typo, renamed node) — warn, or raise?
   Decide during step 3.

## 7. Risks

- **Constructor variance.** Widget constructors are not uniform
  (`Button(rect, label, on_click)` vs `Label(rect, text, font_size, …)`).
  Mitigated by per-type builder functions in the registry rather than a
  blanket `cls(rect, **props)`.
- **Migration behaviour drift.** `MainMenuScene` must run *identically* after
  migration. Mitigated by keeping it the single proving scene this sprint and
  diffing behaviour before/after.

---

## 8. Closeout

**Delivered.** All five planned steps shipped and the existing test suite
passes:

1. `pygame_engine/ui/widget_registry.py` — type→builder registry.
2. `pygame_engine/scene/layout_loader.py` — `LayoutLoader` + live rect binding.
3. `pygame_engine/scene/described_scene.py` — rewritten; resize-ready
   (`screen_rect`, `_rebuild_layout()`, `on_resize()` override).
4. `MainMenuScene` migrated to `DescribedScene`; `layout_builder.py` gained
   the missing `stack()` method; `editor/scene_loader.py` now calls
   `set_screen_rect()`.
5. Decision #25 recorded in `docs/accepted_decisions.md`.

**Scope change during sprint.** `DescribedScene` was made resize-ready
(`on_resize()` rebuilds the layout) — slightly beyond the original step 3,
done so resize support drops in later without reworking the base class.
`L.stack()` was added to `layout_builder.py` to fix a pre-existing DSL gap
surfaced by the migration.

**Post-sprint review.** A full review was run after the five steps
landed; it surfaced follow-up items, all since resolved:

- Tests for the new modules — added: `test_widget_registry.py`,
  `test_layout_loader.py`, `test_described_scene.py`, and
  `test_layout_builder_stack.py`. The full suite passes.
- `SCENE_AUTHORING_GUIDE.md` and `widget_contract.md` described the
  pre-sprint `DescribedScene` and omitted the registry — both rewritten
  to match the shipped engine and decision #25.
- Decision #25 merged into `docs/accepted_decisions.md`; this sprint
  doc relocated from `docs/TODO/` to `docs/sprints/`.
- `game_template` scenes `game_scene`, `pause_scene`, `settings_scene`
  remain plain `Scene`s and now carry a header note: `game_scene` and
  `settings_scene` flagged as migration candidates, `pause_scene` flagged
  as a legitimate plain-`Scene` overlay (per SCENE_AUTHORING_GUIDE.md §1).
- Editor runtime artifacts (`editor/imgui.ini`, `editor/editor_settings.*`)
  added to the root `.gitignore`.

**Genuine deferred work (not sprint-blocking).**

- Evaluate folding `LayoutLoader`'s rect subscriptions into the base
  `Scene.subscriptions` group rather than the separate
  `LoadedLayout.dispose()` path (two teardown mechanisms in one class).
- Migrate `game_scene` and `settings_scene` to `DescribedScene` — later
  work, intentionally out of this sprint's scope.

**Status: closed.** Code, documentation, and tests are aligned; the full
suite passes. The sprint is complete with no outstanding debt.
