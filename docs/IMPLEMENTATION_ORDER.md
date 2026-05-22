---

## Purpose

This document defines the sequence for all planned development work.
Each phase must be fully complete — code, tests, and documentation —
before the next phase begins. The sequence is not arbitrary: it ensures
that each phase builds on a stable, tested foundation.

**Completion criteria for every item:**
- Code written and functioning
- Tests passing (at the tier required by R11)
- Public methods have docstrings
- CHANGELOG.md updated
- This document updated with completion status

---

## Current Status

| Phase | Status | Notes |
|---|---|---|
| Phase A — Foundation Repairs | ✅ Complete | CHANGE-01, 07, 09, 02 all done |
| Phase B — Core Additions | 🟡 In progress | Phase A complete |
| Phase C — Game Codebase Repairs | 🔴 Not started | Depends on Phase A |
| Phase D — Layout and Editor Foundation | ⬜ Planned | Depends on A + B |
| Phase E — Debug and Testing Infrastructure | ⬜ Planned | Depends on B |
| Phase F — Scene Editor | ⬜ Planned | Depends on D + E |
| Phase G — Audio and Input Modules | ⬜ Planned | Depends on B |
| Phase H — Hero Management Game Scenes | ⬜ Planned | Depends on C |
| Phase I — Polish and Deferred Features | ⬜ Planned | Depends on F |

---

## Phase A — Foundation Repairs

**Goal:** Fix current bugs and architectural violations.  
**Gate:** All existing tests pass. Observable property-based tests pass.
No memory leaks detectable in leak tests. Theme singleton removed.

These are repairs to the existing codebase, not new features. They exist
because the design work identified current violations of the restrictions.
The restriction violations must be fixed before building on top of them —
they are architectural debt that compounds if ignored.

| ID | Task | Restriction | Priority |
|---|---|---|---|
| CHANGE-01 | Observable[T] upgrade — weak refs, transaction batching, old-value payload | R09 (memory leak) | ✅ Complete |
| CHANGE-09 | Extend AppConfig: `mode` enum, `reduced_motion: bool` | R09, R18 | ✅ Complete |
| CHANGE-02 | Fix theme singleton — RenderContext Option 2 chosen and implemented | R09 | ✅ Complete |
| CHANGE-07 | SubscriptionGroup class + Scene auto-cleanup on exit | R09 (memory leak) | ✅ Complete |

**Why this order:**
- CHANGE-01 first because everything else builds on it. Its tests must
  be comprehensive before anything depends on it.
- CHANGE-09 before CHANGE-02 because the `mode` enum affects how the
  theme fix is implemented (development vs production behaviour).
- CHANGE-07 after CHANGE-01 because `SubscriptionGroup` is built on
  the upgraded `Observable[T]`.

---

## Phase B — Core Engine Additions

**Goal:** Add new engine capabilities that everything else depends on.  
**Gate:** All existing tests pass. New tests for each addition pass.
Extension hook system verified by loading a test module that uses hooks.

| ID | Task | Blocks |
|---|---|---|
| CHANGE-05 | TimeManager class and `app.time` property | Editor play/stop, pause menus |
| CHANGE-08 | Extension hooks on Application with priority | Editor attachment |
| CHANGE-15 | `widget_id: str | None` field on Widget | Editor selection |
| CHANGE-06 | FocusManager + `tab_index`, `focus_trap` on Widget | Accessibility, editor |
| CHANGE-14 | Atomic writes in SaveManager | Data integrity |

**Why this order:**
- CHANGE-05 and CHANGE-08 are independent and can be done in either order.
- CHANGE-15 is the smallest change — one field. Do it with CHANGE-06.
- CHANGE-06 depends on nothing in this phase.
- CHANGE-14 is independent, low effort. Do it last in this phase.

---

## Phase C — Game Codebase Repairs

**Goal:** Fix restriction violations in the hero management game code.  
**Gate:** All game scenes import from correct locations. `management_scene.py`
is under the hard cap. Scene registry is operational.

These repairs are to game code, not engine code. They do not require the
engine changes from Phases A and B (though some benefit from them). They
can proceed in parallel with Phases A and B where there are no dependencies.

| ID | Task | Restriction | Depends on |
|---|---|---|---|
| CHANGE-03 | Move shared palette to `game/ui/desk_theme.py` and `game/ui/desk_button.py` | R07 | Nothing |
| CHANGE-04 | Decompose `management_scene.py` into panel files | R17 | CHANGE-03 |
| CHANGE-13 | `@register_scene` decorator and scene registry | R07 | Nothing |
| CHANGE-10 | Resolve `col` ambiguity and other abbreviation cleanup | R16 | Nothing |
| CHANGE-11 | Docstring coverage for engine public API | R15 | Phase A (Observable docstrings first) |
| CHANGE-12 | Decompose other long game scene files | R17 | CHANGE-03 |

**Why CHANGE-03 before CHANGE-04:**
The decomposition of `management_scene.py` requires that its shared
palette constants are already in `game/ui/`. Otherwise the decomposed
files would need to import from each other.

---

## Phase D — Layout Descriptor and Editor Foundation

**Goal:** The `DescribedScene` base class exists and works. At least one
game scene is migrated to it. Layout files are read and written correctly.

**Gate:** `DescribedScene` integration test passes. One migrated scene
launches, edits layout, saves to file, and reloads correctly.

**Depends on:** Phase A complete, Phase B CHANGE-01 and CHANGE-15 complete.

| Task | Description |
|---|---|
| `ObservableRect` class | Rectangle that fires one batched event on any coordinate change |
| `ObservableList[T]` class | List that notifies on add/remove/reorder |
| `SceneDescriptor` class | Live observable model of the scene's widget tree |
| `WidgetNode` dataclass | Node in the descriptor tree with all reserved fields |
| `DescribedScene` base class | Optional scene base with descriptor + SubscriptionGroup |
| Layout DSL | `L.panel()`, `L.button()`, `L.dynamic()` context manager |
| `LayoutLoader` | JSON read/write for `SceneDescriptor` |
| Migrate `GameHubScene` to `DescribedScene` | Proof of concept with one real scene |

**Why migrate `GameHubScene` first:**
It is the most frequently visited scene and the simplest in terms of
dynamic content. Validating the descriptor with a real scene before
building the editor ensures the abstraction is correct.

---

## Phase E — Debug and Testing Infrastructure

**Goal:** Developers have gizmo visualisation, a scene test harness,
and a working error scene.

**Gate:** `SceneTestHarness` can load a scene, simulate input, and assert
observable values without a display. GizmoRenderer draws in development
mode and is absent in production mode.

**Depends on:** Phase B complete.

| Task | Description |
|---|---|
| `GizmoRenderer` class | Primitive drawing, gizmo registration, post-render pass |
| `GizmoRenderer` activation | `app.gizmos` property, None in production |
| `ErrorScene` | Built-in error scene for development and production modes |
| Error handling — three categories | Developer errors raise, asset errors emit, runtime errors push ErrorScene |
| `SceneTestHarness` | Headless scene testing — load, advance, press, click, assert |
| Reference test files | `game_template/tests/` examples showing how to test scenes |
| Remote debug server stub | `app.start_debug_server(port)` — read-only widget tree access |
| `preload()` lifecycle method | Asset loading with progress before `on_enter()` |

---

## Phase F — Scene Editor

**Goal:** A working scene editor with viewport, hierarchy, inspector,
gizmos, and play/stop button.

**Gate:** Can open any `DescribedScene`, select widgets by clicking,
inspect their properties, drag to move, and see changes reflected in
the viewport. Play/stop button works correctly.

**Depends on:** Phase D complete, Phase E complete, Phase B CHANGE-08
(extension hooks) complete.

**Note:** This is the largest phase. It should be broken into sub-phases
during implementation.

| Sub-phase | Tasks |
|---|---|
| F1 — Editor shell | ImGui + pygame viewport subsurface, layout |
| F2 — Scene inspection | Hierarchy panel (read-only), inspector (read-only) |
| F3 — Gizmos in viewport | Selection gizmo, camera viewport, grid overlay |
| F4 — Selection | Click to select in viewport and hierarchy, highlight |
| F5 — Transform | Move gizmo (drag), resize gizmo (handle drag) |
| F6 — Inspector editing | Editable fields, `ObservableRect` two-way binding |
| F7 — Undo/redo | Command stack, move command, resize command |
| F8 — Play/stop | TimeManager integration, AudioSnapshot, viewport tint |
| F9 — Auto-save | Every change writes to layout file immediately |
| F10 — Event log panel | Live EventBus events, filter, rate display |
| F11 — Design-time data | Banner when `editor_context()` data is active |
| F12 — Grid snap | 8px base grid, configurable, Shift to bypass |

**F1 before everything:** The editor shell — ImGui window with pygame
subsurface — must work before any panels or gizmos are useful.

**F2 before F3:** Read-only inspection before editing. Validate the
descriptor is correctly read before allowing writes to it.

**F4 before F5:** Selection before transformation. You must be able to
select a widget before you can move it.

**F7 with F5:** Implement the undo command stack when implementing the
first editing gesture (move). Do not add editing without undo.

---

## Phase G — Audio and Input Modules

**Goal:** Audio bus topology works. Music crossfade works. Input recording
is available for automated testing.

**Gate:** Four audio buses (master, music, sfx, ui) with independent
volume control. Music crossfade works. `InputRecorder` records and
replays a simple session.

**Depends on:** Phase B CHANGE-05 (TimeManager for time_scale integration).

| Task | Description |
|---|---|
| Audio bus topology | `AudioBus` class, four default buses on `AudioManager` |
| Bus time_scale integration | Buses pause/resume with `time_scale = 0`/`1` |
| `AudioSnapshot` | Capture and restore bus state across scene transitions |
| `MusicPlayer` module | Crossfade between tracks using the music bus |
| `InputRecorder` module | Record all input events, replay with snapshot resync |

---

## Phase H — Hero Management Game: Remaining Scenes

**Goal:** All game scenes are complete, use `DescribedScene`, are
registered with `@register_scene`, and have basic smoke tests.

**Gate:** All tab bar navigation works in all scenes. Campaign scene
runs without crashing. Mission assignment scene implemented.

**Depends on:** Phase C complete, Phase D complete.

**Remaining scenes to complete or improve:**
- `CampaignMapScene` — functional but untested; add smoke tests
- `MissionAssignmentScene` — not yet ported from original
- All scenes — migrate to `DescribedScene` for editor support
- All scenes — register with `@register_scene`

**Quality improvements for all existing scenes:**
- Replace `_trunc()` calls with `from pygame_engine.graphics.text_utils import truncate`
  (already done for management and hub scenes)
- Ensure all `DeskButton` uses come from `game.ui.desk_button`
- Verify each scene has at least one smoke test

---

## Phase I — Polish and Deferred Features

**Goal:** Quality improvements, deferred features, and editor Phase 2.

**Gate:** No formal gate. This phase is ongoing improvement.

**Depends on:** Phase F complete.

| Task | Notes |
|---|---|
| Anchor system in `WidgetNode` | `AnchorSpec` implementation, editor anchor visualisation |
| Prefab editing in editor | Isolation mode, instance override display |
| Multi-selection in editor | Combined bounding box, shared property editing |
| Alignment and distribution tools | After multi-selection works |
| `save_mode` configuration | `immediate` vs `explicit` for team workflows |
| `preload()` progress display | Customisable loading scene |
| Comprehensive SceneTestHarness tests for all game scenes | Gradual — add per feature |
| ARIA metadata field on Widget | Accessibility preparation |
| Observable value history in inspector | Last N values, timestamps |
| Slow motion control in editor toolbar | `time_scale` slider during play mode |
| Breakpoint observables | Pause when condition met |

---

## What Is Explicitly Not Planned

These are confirmed out of scope and will not appear in any future phase
unless the engine's scope changes through a documented design decision.

- Visual scripting
- Sandboxed plugin system
- Animation timeline editor
- Automatic Python hot reload
- Physics engine
- Networking layer in core
- 3D rendering
- Editor shipping with game binary

---

## How to Use This Document

**When starting a new task:**
1. Check which phase it belongs to
2. Verify all phase dependencies are complete
3. Check CODEBASE_CHANGES.md for any blocking changes that apply
4. Read the DESIGN_SPEC.md section for the feature being built
5. Check RESTRICTIONS.md for any restrictions that apply

**When completing a task:**
1. Mark it complete in this document
2. Update CODEBASE_CHANGES.md if it was a tracked change
3. Update CHANGELOG.md with a concise entry
4. If the change affects architecture, update DESIGN_SPEC.md
5. Verify the gate conditions for the phase are met before declaring
   the phase complete