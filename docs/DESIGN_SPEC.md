# pygame_engine — Complete Design Specification

**Version:** 2.0-design  
**Status:** Active design document — referenced during all development  
**Last updated:** May 2026

---

## Table of Contents

1. [Guiding Principles](#1-guiding-principles)
2. [Three-Circle Architecture Model](#2-three-circle-architecture-model)
3. [Engine Core — What Exists and What Changes](#3-engine-core)
4. [Engine Modules — Planned Additions](#4-engine-modules)
5. [Deferred — Designed For, Not Built](#5-deferred)
6. [Explicitly Out of Scope](#6-explicitly-out-of-scope)
7. [Implementation Restrictions](#7-implementation-restrictions)
8. [Required Codebase Changes](#8-required-codebase-changes)
9. [Implementation Order](#9-implementation-order)
10. [Open Questions](#10-open-questions)

---

## 1. Guiding Principles

These govern every decision. When a tradeoff arises, return here first.

### The Modularity Test

Before any concept enters the engine, ask:

> "Can a developer building a completely different game — a Tetris clone,
> a visual novel, a simulation — use this without modification?"

If the answer requires mental gymnastics, it belongs in the game layer, not
the engine. This test is applied to every new class, method, and module.

### The Same Code Path Rule

The editor and the game must use exactly the same rendering and update code
paths. No editor-only simulations of game behaviour. No divergence between
play mode and real execution. If the editor wraps a scene, it wraps the
actual scene class running the actual game code.

### Progressive Disclosure

The engine exposes the minimum necessary by default. Advanced features are
revealed explicitly. A new developer should be productive within an hour.
Complexity earns its place — it is not assumed.

### Correctness Over Convenience

Shortcuts that are easy to replace later are acceptable. Shortcuts that
become load-bearing walls are not. The question to ask: "Does this choice
make the system harder or easier to change in six months?"

### One Way to Do Each Thing

At each level of abstraction, there is exactly one idiomatic way to
accomplish a task. Multiple valid approaches produce inconsistent codebases
and documentation overhead. When two approaches exist, one is the right one
and the other is internal or deprecated.

---

## 2. Three-Circle Architecture Model

```
┌─────────────────────────────────────────────────────────────┐
│  Game Code                                                  │
│  Specific to one game. Contributes nothing back.            │
│  Scenes, systems, models, game state, game UI.              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Engine Modules (Optional)                          │   │
│  │  Independent capabilities many games need.          │   │
│  │  Editor, MusicPlayer, InputRecorder, TestHarness.   │   │
│  │                                                     │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │  Engine Core (Non-optional)                   │  │   │
│  │  │  Primitives any interactive application needs. │  │   │
│  │  │  Application, Scene, Widget, Observable,       │  │   │
│  │  │  EventBus, TimeManager, InputManager,          │  │   │
│  │  │  AudioManager, AssetManager, SaveManager,      │  │   │
│  │  │  FocusManager, GizmoRenderer.                  │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Dependency rule:** Arrows only point inward. Game code imports from modules
and core. Modules import from core only. Core imports from nothing above it.
Delete the outermost circle and the inner circles still work. This is enforced
by CI — see Restriction 2 and Restriction 8.

**Layer definitions for the dependency direction restriction:**

```
Layer 0 — Primitives
  Observable, EventBus, TimeManager, AssetManager, SaveManager
  No dependencies on any other engine layer.

Layer 1 — Core systems
  Widget, Scene, InputManager, AudioManager, FocusManager
  May import from Layer 0 only.

Layer 2 — Composite systems
  SceneManager, Panel, Stack, DescribedScene, GizmoRenderer
  May import from Layer 0 and Layer 1.

Layer 3 — Optional modules
  Editor, MusicPlayer, InputRecorder, SceneTestHarness
  May import from any layer. Game code must not import from Layer 3
  except in explicit development-only code paths.
```

---

## 3. Engine Core

### 3.1 Application

The central object owning the window, the game loop, and all engine systems.

**Current state:** Exists. Stable. Works correctly.

**Changes required:**

- Add extension hooks (see below) — additive, no breaking changes
- `app.time` property returning `TimeManager` — currently `dt` is computed
  inline and not exposed. This is a required addition.
- `app.gizmos` property returning `GizmoRenderer | None` — new
- `app.focus` property returning `FocusManager` — new
- `app.mode` property — extend existing `debug: bool` to
  `mode: Literal["development", "production", "testing"]`
- `app.reduced_motion: bool` — new, checked by all animations

**Extension hooks — new:**
```python
app.on_startup:      list[Callable]
app.on_shutdown:     list[Callable]
app.on_pre_update:   list[Callable[[float], None]]
app.on_post_update:  list[Callable[[float], None]]
app.on_pre_render:   list[Callable[[Surface], None]]
app.on_post_render:  list[Callable[[Surface], None]]    # priority: int = 0
app.on_scene_push:   list[Callable[[Scene], None]]
app.on_scene_pop:    list[Callable[[Scene], None]]
```

Each hook entry supports an optional `priority: int`. Higher priority runs
later. This makes ordering deterministic without extensions knowing about
each other.

**Why extension hooks instead of subclassing Application:**
Optional modules must not require subclassing the core `Application` class.
Subclassing couples the module to Application's internal inheritance structure.
Hook registration is a data operation — modules append callables to a list.
This matches Flask's extension pattern and scales cleanly.

### 3.2 TimeManager

**Current state:** Does not exist as a named class. `dt` is computed inline
in the application loop and passed to `scene.update(dt)`. Time-related
values — `self._t` accumulators in scenes — are managed ad-hoc.

**Why this is needed:** Consistency and controllability. Multiple scenes
manage their own time accumulators differently. There is no way to pause
all game logic (set `time_scale = 0`) without modifying every scene.
The editor's play/stop button requires `time_scale` control. Slow-motion
debugging requires it. Any future pause-menu-that-pauses-the-game requires it.

**Required new class:**
```python
class TimeManager:
    time_scale:          float   # 0=paused, 1=normal, 0.5=slow motion
    delta_time:          float   # dt * time_scale — passed to scene.update()
    unscaled_delta_time: float   # raw dt — for UI, editor, audio UI bus
    time:                float   # total scaled time since startup
    unscaled_time:       float   # total raw time since startup
    frame_count:         int     # total frames rendered
    max_delta_time:      float   # clamp — prevents spiral of death

    def register_fixed_step(self, callback, rate: int = 60) -> None:
        """Register a callback that fires at a fixed rate regardless of render fps."""
```

`time_scale` is an `Observable[float]`. Audio buses, animations, and the
editor play button all subscribe to changes.

**Impact on existing code:** Every scene's `self._t += dt` pattern becomes
`self._t += dt` where `dt` is already the scaled value — no change needed
in scenes. The `dt` they receive changes meaning (it is now scaled), which
is what we want.

### 3.3 Observable System

**Current state:** `Observable[T]` exists in `state/observable.py`. Used
for reactive values. Works but is missing three critical features.

**Why upgrades are needed:**

1. **Weak reference subscriptions** — without them, a scene that subscribes
   to an observable and is then popped from the stack is never garbage
   collected. The observable holds a strong reference to the scene's
   callback. This is a memory leak that compounds with every scene
   navigation. This is a current bug, not a future concern.

2. **Transaction batching** — without it, setting four properties on a
   widget fires four events. The undo system receives four commands instead
   of one "move" command. The inspector redraws four times. Event storms
   are possible.

3. **Old value in event payload** — the undo system must know what a value
   was before it changed, not just what it changed to. The current
   `Observable[T]` only passes the new value to subscribers.

**Required changes to `Observable[T]`:**
- Subscribers held via `weakref`. Destroyed objects auto-unsubscribed.
- `observable.transaction()` context manager — batches changes, fires
  one event at the end with (old_value, new_value).
- Subscriber callbacks receive `(old_value, new_value)` instead of
  just `(new_value,)`. **This is a breaking change to the subscriber
  signature.** All existing subscribers must be updated.

**New class — `ObservableRect`:**
```python
class ObservableRect:
    x, y, w, h: int
    def set(self, x, y, w, h) -> None   # fires one batched event
    def to_pygame_rect(self) -> pygame.Rect
    def transaction(self) -> ContextManager
    def subscribe(self, callback) -> Token
```

**New class — `SubscriptionGroup`:**
```python
class SubscriptionGroup:
    def add(self, token: Token) -> Token
    def on(self, bus: EventBus, event_name: str, callback) -> Token
    def dispose(self) -> None  # cancels all subscriptions
```

The `Scene` base class gains `self.subscriptions: SubscriptionGroup` that
is automatically disposed in `on_exit()`. This eliminates all manual
unsubscription boilerplate.

**Priority:** The Observable upgrade must be the first implementation task.
Everything else builds on top of it. It needs comprehensive tests — including
property-based tests via Hypothesis — before any other feature is built.

### 3.4 EventBus

**Current state:** Exists. Works well. Used throughout.

**Changes required:**

- Typed event payloads — events should carry typed dataclass payloads,
  not raw kwargs. This is a design goal for new events. Existing events
  are grandfathered.
- Middleware — `bus.use(middleware_fn)` for extensions that need to
  intercept all events. Used by the editor's event log panel.
- Subscription via `SubscriptionGroup` — `self.subscriptions.on(bus, ...)`.

**Why typed payloads:** Raw kwargs are invisible to type checkers, not
introspectable, and undocumented. A typed `@dataclass` payload is
self-documenting and can be validated. New engine events use typed payloads.
Existing events are not changed to avoid breakage.

### 3.5 Scene Lifecycle

**Current state:** `on_enter`, `update`, `render`, `on_exit`, `on_pause`,
`on_resume`, `on_resize` all exist.

**Changes required:**

- `preload()` method — returns `list[AssetRequest]`. Engine loads assets
  while showing a loading scene. Called before `on_enter()`.
- `SubscriptionGroup` auto-disposed on `on_exit()`.
- Stack depth limit: 8 default, configurable. `SceneStackDepthError` in
  development mode, silent pop in production.
- `editor_context()` classmethod — returns `dict`. Used by editor to
  provide mock data when running a scene in edit mode. Default returns `{}`.

**Why `preload()`:** Without it, `on_enter()` loads assets synchronously
before the first render. Large assets freeze the display. `preload()` allows
the engine to show a loading indicator with progress while assets load.
This is especially important for scenes with many assets.

### 3.6 Widget

**Current state:** Solid foundation. Needs minor additions.

**Additions (non-breaking):**
```python
Widget:
    widget_id:    str | None = None    # stable editor identifier
    tab_index:    int | None = None    # None = natural tab order
    focus_trap:   bool = False         # traps tab nav within this widget
    editor_tags:  list[str] = []       # for hierarchy panel filtering
```

`widget_id` is the key the editor uses to identify widgets across reloads.
Python's `id(widget)` changes when a widget is recreated — `widget_id` is
stable because it's assigned by the scene, not by Python's memory allocator.

**Why not `editor_id`:** The field name should be `widget_id` because it
describes what the widget is, not where it's used. The editor uses it but
it's not an editor concept — it's an identity concept.

### 3.7 FocusManager

**Current state:** Focus state is managed by individual `Panel` widgets.
`Widget.focused`, `Widget.focusable`, and tab traversal exist in panels.

**Why a centralised FocusManager:** The current approach means each panel
manages its own focus independently. There is no way to ask "what is
currently focused?" globally. There is no way to set focus programmatically
from outside the panel. Modal dialogs cannot trap focus reliably because
focus trapping is not coordinated.

**Required new class:**
```python
class FocusManager:
    focused:            Widget | None
    focus_ring_colour:  tuple
    focus_ring_width:   int

    def set_focus(self, widget: Widget) -> None
    def clear_focus(self) -> None
    def next_focus(self) -> None    # tab forward
    def prev_focus(self) -> None    # shift-tab backward
```

Focus ring is drawn by `FocusManager` as a post-render pass. Individual
widgets do not draw their own focus ring. `ui.focus.changed` event emitted
on bus when focus moves.

`focus_trap = True` on a widget means tab navigation never escapes it —
used by `ConfirmDialog` and any modal overlay.

### 3.8 AudioManager

**Current state:** Exists. Provides music/SFX volume, mute, basic playback.

**Why bus topology:** Games need independent volume control per sound
category. Master, Music, SFX, UI. A player muting music should not affect
UI sounds. A pause menu should silence SFX but not UI. This is impossible
without buses. Every real game needs this eventually.

**Required additions:**
```python
class AudioBus:
    volume:                   Observable[float]
    muted:                    Observable[bool]
    pitch:                    float
    respects_time_scale:      bool    # default True
    pitch_follows_time_scale: bool    # default False
    def play(self, source: AudioSource) -> PlaybackHandle
    def stop_all(self) -> None

class AudioManager:
    master: AudioBus
    music:  AudioBus
    sfx:    AudioBus
    ui:     AudioBus
    def create_bus(self, name: str, parent: AudioBus) -> AudioBus
```

**Bus time scale behaviour:** When `time_scale = 0`, music and SFX buses
pause. UI bus continues — menu button sounds still work during game pause.
Each bus controls this via `respects_time_scale`.

### 3.9 AssetManager

**Current state:** `AssetLoader` exists with lazy caching.

**Changes required:**

- `resolve(path: str) -> Path` — single method that knows whether running
  in development or from a frozen PyInstaller executable. This is the only
  place in the entire codebase that touches this distinction.
- Standard project layout expected by default: `assets/`, `data/`, `saves/`
  at project root. Fully configurable via `AppConfig`.
- No direct `open()` calls anywhere else in engine or game code — all file
  access goes through `AssetManager.resolve()`.

### 3.10 SaveManager

**Current state:** Persistence infrastructure exists in `persistence/`.

**Changes required:**

- Atomic writes — write to temp file, then rename. Prevents corruption from
  interrupted saves. This is a correctness fix, not a new feature.
- `auto_save(interval: float, callback: Callable[[], dict]) -> None`
- Abstract `backend` property — defaults to local file system. Cloud save
  can be implemented as an alternative backend without changing the
  `SaveManager` interface.

### 3.11 GizmoRenderer

**Current state:** Does not exist.

**Why needed:** Debug visualisation — collision boxes, camera bounds,
trigger zones, pathfinding grids, selection handles — is a universal need
across game development. Without a gizmo system, developers add temporary
debug drawing to their scene `render()` methods and forget to remove it.
Gizmos are the right place for this: always visible in development mode,
zero cost in production.

```python
class GizmoRenderer:
    enabled:    bool
    categories: set[str]    # filter which gizmo categories draw
    def draw_rect(self, rect, colour, label=None, dashed=False) -> None
    def draw_circle(self, pos, radius, colour) -> None
    def draw_line(self, start, end, colour) -> None
    def draw_arrow(self, start, end, colour) -> None
    def draw_text(self, pos, text, colour) -> None
    def register(self, gizmo: Gizmo) -> None
    def unregister(self, gizmo: Gizmo) -> None
```

`app.gizmos` is `None` in production mode. Zero cost. Activated in
development mode and editor mode. Games and the editor register `Gizmo`
objects. Engine calls `gizmo.draw(renderer, camera)` in a post-render pass.

### 3.12 Error Handling

**Current state:** Exceptions propagate. `crash_log` captures unhandled
exceptions. No in-engine error recovery.

**Required approach — three error categories:**

**Developer errors** — wrong API usage, missing required parameters. Raise
`EngineError` immediately with a clear descriptive message. Never silent.
These should be caught in development, never reach players.

**Asset errors** — missing file, corrupt data. Substitute placeholder.
Emit `engine.asset.error` on EventBus. Keep running.

**Runtime errors** — scene throws during `update()` or `render()`. Catch.
Log full stack trace. Emit `engine.scene.error` on bus. Push `ErrorScene`.
In development: shows stack trace. In production: shows game-configured
message. In testing: re-raises for pytest to catch.

`AppConfig.error_scene_class` — games provide their own error scene.
Engine has a default.

---

## 4. Engine Modules

Optional. Independently activatable. None depends on another module —
only on the core. Activated through the extension hook system.

### 4.1 DescribedScene and Layout Descriptor System

The bridge between code-defined layout and the scene editor.

**What it is:** An optional base class that scenes inherit from if they want
editor support. Scenes that do not inherit it work identically — no
degradation.

```python
class DescribedScene(Scene):
    @classmethod
    def editor_context(cls) -> dict:
        """Override to provide mock data for editor preview."""
        return {}

    def _build_layout(self) -> None:
        """Override to populate self.layout with widget descriptors."""
        ...

    layout:        SceneDescriptor      # the live observable model
    subscriptions: SubscriptionGroup    # auto-disposed on exit
```

**SceneDescriptor:**
```python
class SceneDescriptor:
    nodes:              dict[str, WidgetNode]
    root:               WidgetNode
    on_any_change:      Observable
    on_structure_change:Observable
    def load(self, path: Path) -> None
    def save(self, path: Path) -> None
    def load_or_default(self, path: Path, build_fn) -> None
```

**WidgetNode:**
```python
@dataclass
class WidgetNode:
    widget_id:        str
    type:             str
    rect:             ObservableRect
    props:            dict[str, Observable]
    children:         ObservableList[WidgetNode]
    parent:           WidgetNode | None
    anchor:           AnchorSpec | None      # reserved — not yet implemented
    prefab_source:    str | None             # reserved — path to source layout
    prefab_overrides: dict                   # reserved — per-instance overrides
    editor_only:      bool                   # true for organisational folders
    editor_tags:      list[str]
    editor_visible:   bool
    editor_locked:    bool
```

**Layout DSL:**
```python
def _build_layout(self):
    with self.layout() as L:
        L.panel("recruits_panel", x=8, y=64, w=620, h=760)
        L.dynamic("hero_rows", parent="recruits_panel",
                   placeholder_count=5, placeholder_height=72)
        L.button("resolve_btn", x=1700, y=36, w=160, h=32,
                  label="Resolve Round")
```

`L.dynamic()` declares a region filled by code at runtime. Editor shows
placeholder rows. Code fills with real data. The boundary is explicit.

**Bidirectional sync:**
- Code changes `_build_layout()` → editor detects file change → re-runs
  `_build_layout()` on existing scene instance → observable changes
  propagate to inspector and viewport
- Editor drags widget → `ObservableRect` fires → scene updates widget rect
  → layout file written immediately

**Hot reload scope:** Layout descriptor reloads when the layout JSON file
changes on disk. Python modules are never hot-reloaded automatically.
Avoids Python module reload fragility entirely.

**Prefabs as instanced layout files:**
```python
L.instance("party_panel", source="layouts/party_panel.layout.json", x=640, y=64)
```
No separate prefab asset type. Layout files are the unit of reuse. The
editor shows instanced layouts with a distinct icon.

**Layout file format:** JSON. Keys ordered consistently. Default values
omitted. Schema version field in every file. Produces minimal VCS diffs.

### 4.2 Scene Editor

The visual editing layer. Completely optional. The game has zero knowledge
of the editor's existence.

**Architecture:**
```
editor/
  editor_app.py          # EditorApplication wrapping Application
  panels/
    hierarchy.py         # ImGui tree view of widget tree
    inspector.py         # ImGui property editor for selected widget
    toolbar.py           # tools, play/stop, grid controls
    event_log.py         # live EventBus event visualisation
    remote_inspector.py  # connects to running game debug server
  gizmos/
    selection.py         # handles on selected widget
    trigger_box.py       # coloured overlays for collision zones
    camera_viewport.py   # rectangle showing camera bounds
    grid.py              # snap grid overlay
  commands/
    move.py
    resize.py
    reparent.py
    add_widget.py
    delete_widget.py
    undo_stack.py
  layout_io.py           # JSON read/write for SceneDescriptor
```

**Why ImGui for editor panels:** Building the editor's hierarchy panel,
inspector, toolbar, and docking system using our own engine widgets would
take months before writing a line of actual editor logic. Dear ImGui exists
specifically for this use case and is used internally at many game studios.
The split is clean: pygame owns the game viewport subsurface, ImGui owns
the surrounding panels. The game is entirely unaware of ImGui.

**Game viewport:** The game scene renders into a pygame subsurface. The
editor draws this surface as an ImGui image widget. Same rendering code as
the real game.

**Edit mode:** `time_scale = 0`. Scene receives `dt = 0` — nothing moves.
Editor animations use `unscaled_delta_time` and continue running.
All editor input is active. Inspector and hierarchy are fully editable.

**Play mode:**
```
Press Play:
  1. AudioSnapshot captured
  2. Layout descriptor snapshotted to memory
  3. Scene reinitialised with editor_context() data
  4. time_scale = 1.0
  5. Input routed exclusively to game scene
  6. Editor input disabled — no clicks, drags, or keyboard shortcuts
  7. Viewport tinted (configurable colour, default blue)
  8. Inspector switches to read-only display of live observable values
  9. Hierarchy switches to read-only display
  10. Toolbar shows: Stop, Pause, frame counter, elapsed time

Press Stop:
  1. time_scale = 0
  2. Layout descriptor restored from snapshot
  3. AudioSnapshot restored
  4. Scene reinitialised with editor_context() data
  5. Editor input re-enabled
  6. Inspector and hierarchy return to editable state
  7. Tint removed
  8. All game state from play session discarded
```

**Play mode is read-only.** The editor does not allow widget editing during
play mode. Play mode tests what has been built, not makes permanent changes
while the game is running. This eliminates the entire conflict resolution
problem for simultaneous writers.

**Why this is the right decision:** Unity allows editing during play mode
and shows a warning "changes will be lost." This warning exists because
allowing edits was a mistake they cannot remove for backwards compatibility.
We make the correct decision upfront.

**Inspector during play mode:** Fields are read-only but show live observable
values updating in real time. Observable values are colour-coded:
- Static — normal text colour
- Recently changed — brief amber highlight, fades back
- Rapidly changing — persistent amber, shows rate per second
- This session min/max — shown on hover

**Undo/redo:** Full command stack. Every edit is a `Command` with
`execute()` and `undo()`. Commands reference widgets by `widget_id`, not
Python object reference. Commands are serialisable — undo survives a reload.

**Auto-save:** Every change writes through immediately to the layout file.
There is no "unsaved" state. The undo stack is the safety net.

**Save mode for teams:** `editor_mode: Literal["immediate", "explicit"]`
in project settings. `immediate` is the default (auto-save). `explicit`
accumulates changes in memory and requires a manual Save action — designed
for teams where the layout file is a VCS artifact.

**Hierarchy panel features:**
- Search by widget_id or type
- Filter by type, visibility, lock state, tags
- Drag to reorder — changes Z-order
- Eye icon — editor visibility toggle
- Lock icon — prevent selection and editing
- Editor-only organisational folders (not in runtime scene graph)
- Instanced layout files shown with distinct icon, openable in new tab

**Editor-only organisational folders:** Groups that exist only in the
hierarchy for organisation. Stored in layout file with `editor_only: true`.
Discarded by the engine at runtime. Zero cost.

**Multi-selection inspector:** Shared properties shown as editable.
Type-specific properties grouped and collapsed. Mixed values shown as
dashes, not blank.

**Inspector customisation per widget type:** Each widget type declares its
own inspector layout. No generic field dump. Widget authors define which
properties appear, in what order, with what controls.

**Event log panel:** Shows EventBus events firing in real time. Event name,
payload, timestamp, subscriber count, events per second. Highlights events
with no subscribers (potential bugs) and events firing more than N times
per second (potential storms).

**Remote debug inspector:**
```python
app.start_debug_server(port=7777)  # in game code, development only
```
Editor connects and reads live widget tree and observable values. Read-only.
No control. Works with a separately running game — distinct from play mode.

**Prefab isolation mode:** When editing an instanced layout file, the main
scene dims and only the instanced file is interactive. Two edit contexts
maintained simultaneously.

**Gizmo layer in editor:**
- Selection handles — move (body drag), resize (edge and corner handles)
- 8px base grid with snap — configurable, Shift to bypass
- Camera viewport rectangle
- Trigger box visualisation — coloured semi-transparent rects, dashed border
- Lighting toggle — show scene with or without lighting pass
- Anchor visualisation — arrows indicating anchored edges (reserved)

**Design-time data banner:** Visible banner in viewport when
`editor_context()` data is active — "Preview: using editor context data."
Prevents confusion between preview and real data.

**Play mode tint:** Configurable colour applied to viewport during play
mode. Prevents the common mistake of making layout edits during play.

**Binding indicators in inspector:** Observable properties show a binding
state dot — green (bound, receiving values), amber (bound, no value yet),
grey (unbound).

**Progressive disclosure:** Default layout shows minimum panels. Advanced
panels revealed explicitly. A new developer should be productive within
an hour.

**RestrictedApplication facade:** In editor mode, the game scene receives
a `RestrictedApplication` wrapper instead of the real `Application`.
Intercepts dangerous calls — direct display access, direct quit calls —
that could destabilise the editor. Transparent for all legitimate scene
uses.

### 4.3 InputRecorder

Records and replays input sessions. Transparent to all code above
`InputManager`. Activated by setting `app.input.recorder` — the game and
all scenes are completely unaware.

**Use cases:**
- Automated testing — record, replay, assert state matches
- Bug reproduction — low-overhead always-running recorder captures last N seconds
- Demo recording — attract mode, tutorials

**Determinism:** Not promised. State snapshots taken at configurable
intervals during recording. Playback resyncs from the nearest snapshot
if drift is detected.

### 4.4 MusicPlayer

Dynamic music transitions on top of the AudioManager bus system.
Crossfade is the baseline. Layered music and adaptive sequencing built
on the same interface.

### 4.5 SceneTestHarness

Testing utility for game developers. Lives in `pygame_engine.testing` —
stable public API tier.

```python
class SceneTestHarness:
    def load(self, scene_class, context: dict = {}) -> None
    def advance(self, dt: float) -> None
    def press_key(self, key: int) -> None
    def release_key(self, key: int) -> None
    def click(self, pos: tuple) -> None
    def scroll(self, pos: tuple, dy: int) -> None
    def assert_widget(self, widget_id, rect=None, visible=None) -> None
    def assert_event_emitted(self, event_name) -> None
    def assert_observable(self, observable, value) -> None
    def screenshot(self) -> Surface
```

Headless by default (`SDL_VIDEODRIVER=dummy`). Each test gets a fresh
scene instance. Reference test files in `game_template/tests/`.

---

## 5. Deferred — Designed For, Not Built

These are not being built now. Architecture reserves space for them.

| Feature | Reserved as | Notes |
|---|---|---|
| Anchor system | `anchor: null` field in `WidgetNode` | Phase 2 of layout |
| Constraint solver | Not blocked by anchor field | Post-anchor |
| Prefab instance overrides | `prefab_overrides: {}` in `WidgetNode` | Reserved |
| Cloud saves | Abstract `SaveBackend` in `SaveManager` | Swap backend |
| Networking | State serialisability enforced now | Additive module |
| RTL text | Rendering pipeline not blocked | No LTR assumptions |
| Smart guides in editor | Phase 2 after basic drag works | Low priority |
| Multi-selection | Phase 2 | Complex gizmo system |
| Alignment tools | Phase 2 | After multi-selection |
| Fixed timestep | `register_fixed_step()` stub | For deterministic systems |
| Screen reader | ARIA metadata field in Widget | Deferred |

---

## 6. Explicitly Out of Scope

These will not be built. Documented so future decisions do not relitigate.

| Feature | Reason |
|---|---|
| Visual scripting | Python is the scripting language |
| Sandboxed plugins | Developer tool, not an app store |
| Animation timeline editor | Separate product-level effort |
| Automatic Python hot reload | Fragile; replaced by descriptor reload |
| Networking in core | Optional future module, not core |
| RTL text (near term) | Deferred; pipeline not blocked |
| Editor shipping with game | Dev tool only |
| Physics engine | Out of scope; use pymunk |
| 3D rendering | Out of scope |

---

## 7. Implementation Restrictions

These are architectural rules enforced by CI, linters, or code review.
Not suggestions — violations require justification and consensus.

---

### R01 — Behaviour Must Be Statically Traceable

**Rule:** No `eval()`, no `exec()`, no dynamic class creation in production
code paths. Any developer should be able to read the code and trace exactly
what will happen at runtime without executing it.

**Why:** Code generation makes behaviour unpredictable, untestable, and
undebuggable. It breaks type checking and static analysis. Generated code
is by definition a different code path from what the developer wrote.

**Scope:** Production code paths. Debug tools and the editor may use
introspection — they are development-only tools and are entirely within
`editor/` and `testing/` modules.

**Permits:** The layout descriptor loading JSON into typed Python objects
(data loading, not code generation). The `@register_scene` decorator
(a registry pattern, not code generation). Lookup dicts for type mapping.

---

### R02 — No Circular Dependencies

**Rule:** The engine module import graph must be a DAG. No module imports
from a module that eventually imports from it.

**Why:** Circular imports in Python produce subtle, hard-to-debug errors.
They make import order matter, create partially-initialised modules, and
make it impossible to understand what depends on what.

**Enforcement:** CI script imports every engine module in isolation.
Fails the build if any circular imports are detected. Runs on every commit.
Zero exceptions.

---

### R03 — Dependency Direction is Explicit

**Rule:** Lower layers never import from higher layers. See the layer
definitions in Section 2. A Layer 0 module cannot import from Layer 1.

**Why:** Without a stated dependency direction, the import graph can become
correct (no cycles) but tangled. A `Observable` importing from `Widget`
to check if a subscriber is a widget would be a layering violation even
without creating a cycle.

**Enforcement:** The CI circular dependency check catches most violations.
An additional layering check script validates import paths against the
stated hierarchy.

---

### R04 — Engine Has No Opinions About Game Data

**Rule:** The engine does not define what a hero, gold, contract, inventory,
or any game-specific concept is — not even as an abstract base class,
not even as a type hint, not even in a comment used as an example.

**Why:** Every game-specific concept that enters the engine becomes a
constraint on every future game built with it. Engines that start general
and drift specific are a well-documented failure mode.

**The test:** Before any new concept enters the engine, apply the modularity
test. If a Tetris developer or visual novel developer cannot use it without
modification, it belongs in the game layer.

**Permits:** `SaveManager` that saves any dict. `Observable[T]` that holds
any value. `Entity` with any components. Generic containers that the game
fills with meaning.

---

### R05 — Public API Grows Deliberately and Consistently

**Rule:** No new public API is added without explicitly passing three tests:
1. Does this pass the modularity test?
2. Are we prepared to maintain backwards compatibility for this indefinitely?
3. Can this serve at least two different hypothetical games?

Additionally: each addition must be the single idiomatic way to accomplish
its purpose. No addition creates a second way to do something already in
the public API.

**Why:** Public APIs are promises. The larger the stable tier, the more
constrained future development becomes. Keep it small and deliberate.

**Pre-1.0 note:** The bar for question 3 is "probably yes" during active
development. After 1.0, concrete examples of two different game use cases
are required.

---

### R06 — Configuration Uses Data, Not Subclassing

**Rule:** When the engine needs to be configurable, configuration is
expressed as data (parameters, dicts, dataclasses) not as subclasses
to override methods on.

**Why:** Subclass-based configuration couples game code to the engine's
internal inheritance structure. Data-based configuration is looser — the
engine defines the interface, the game provides values.

**Exception:** `Scene` and `Widget` are explicitly designed for subclassing.
This restriction applies to configuration and extension points, not to the
core abstractions.

---

### R07 — Scenes Do Not Import Each Other

**Rule:** Scene files must not import another scene class at module level.
Navigation uses the scene registry or lazy imports inside method bodies.

**Why:** Cross-scene imports create a dependency web that makes individual
scenes impossible to test in isolation and makes the import graph fragile.
Even non-circular cross-scene imports create tight coupling.

**Correct pattern:**
```python
def _go_to_hub(self):
    from game.scenes.game_hub_scene import GameHubScene  # lazy, inside method
    self._app.scene_manager.replace_with(GameHubScene(...))
```

Or preferably via the scene registry when implemented:
```python
def _go_to_hub(self):
    Cls = scene_registry.get("GameHubScene")
    self._app.scene_manager.replace_with(Cls(...))
```

---

### R08 — Maximum Inheritance Depth of Three

**Rule:** No class in the engine or game should be more than three levels
deep in an inheritance hierarchy.

```
Widget           # depth 1
  Panel          # depth 2
    ScrollPanel  # depth 3 ← maximum
```

**Why:** Deep hierarchies make code hard to read, hard to change, and hard
to test. Understanding a class at depth 4 requires reading four class
definitions.

**Alternative:** When depth would exceed three, use composition instead.
A class that needs behaviour from more than two parents needs decomposition.

**Mixin rule:** Mixins are permitted at depth two only. A mixin applied to
a class that's already a mixin applied to a base is always a design smell.

---

### R09 — No Stateful Singletons in the Engine

**Rule:** The engine must not use module-level mutable state. Global
variables, module-level caches, singleton instances that persist across
`Application` instantiations are not permitted.

**Why:** Two `Application` instances in the same process — which happens
in tests and in the editor — must not share state. The current `get_theme()`
is a violation of this rule that must be fixed.

**Current violation:** `get_theme()` in `theme/runtime.py` accesses a
module-level singleton. This is the highest-priority violation to fix.

**Correct pattern:** All engine state lives on the `Application` instance.
Widgets receive what they need through parameters or a context object
passed at render time, not by reaching into a global.

**Exception:** `bus` (EventBus singleton) and `flags` (RuntimeFlags
singleton) are explicitly accepted by existing decision 23. These are
grandfathered. No new singletons.

---

### R10 — Widget Render Methods Must Be Pure Given State

**Rule:** A widget's `render(surface)` must produce identical output every
time it's called with the same widget state and the same surface.

**Why:** This enables dirty flag caching, screenshot regression testing,
editor static preview, and surface caching. The current `TextBlock` caching
already assumes this — the restriction formalises the assumption.

**Animated widgets:** Animation is achieved through state changes driven
by `update(dt)`, not through time-dependent rendering. The render method
sees current state only.

**Violation to watch for:**
```python
def render(self, surface):
    phase = math.sin(pygame.time.get_ticks() * 0.001)  # violation — reads clock
```

**Correct pattern:**
```python
def update(self, dt):
    self._phase += dt  # state changes in update

def render(self, surface):
    phase = math.sin(self._phase)  # reads state, not clock
```

---

### R11 — No Feature Without a Test (Tiered by Context)

**Rule:** Every engine addition must have tests in the same session.
The required depth depends on context:

**Engine core:** Full coverage. Happy path, edge cases, failure modes,
cleanup verification. Property-based tests for complex logic (Hypothesis).

**Engine modules:** Integration tests showing the module works with core.
Unit tests for non-trivial internal logic.

**Game scenes:** Smoke tests only — does the scene instantiate, enter,
and exit without crashing?

**Debug tools and editor:** Best effort. Test stable interfaces, not
implementation details.

**Why now, not later:** Features without tests are hypotheses. An engine
bug affects every game built on it. The asymmetry justifies the discipline.

---

### R12 — No Silent Failures

**Rule:** Every operation either succeeds visibly or fails visibly.
Nothing is left in an undefined intermediate state.

**Success** means the stated postconditions hold.
**Failure** means either:
- An exception is raised (for developer errors)
- A failure event is emitted on the bus (for recoverable errors)

Never: a function that does nothing, returns a wrong value, or logs
to stderr without emitting an event — these are silent failures.

**Postconditions:** Public methods should document their postconditions.
"After `subscribe()`, the callback will be called on every change." These
must be tested, not just documented.

---

### R13 — No Game Logic Threading

**Rule:** Game logic runs on the main thread only. No background threads
for scene updates, observable propagation, or game state mutation.

**Why:** Threading in Python with shared mutable state is a source of
non-deterministic bugs that are nearly impossible to reproduce. The GIL
mitigates some issues but not all.

**Permitted on background threads:**
- Asset loading during `preload()` — reads files, no shared mutable state
- Audio streaming — managed by pygame-ce's subsystem
- The debug server — read-only access to widget tree
- Input recorder buffer — append-only, carefully synchronised

**Alternative for expensive operations:** Coroutines (async/await on main
thread) or a frame-budget system spreading work across frames.

**Note:** `async/await` coroutines on the main thread are permitted. They
are cooperative multitasking within a single thread, not threading.

**Future review:** If the engine's target games expand significantly toward
action or simulation genres with expensive per-frame computation, this
restriction is the first to revisit.

---

### R14 — Editor is Always Optional, Enforced by CI

**Rule:** Deleting the `editor/` directory entirely must not cause any
test to fail or any engine import to fail.

**Enforcement:** CI job runs the full test suite with `editor/` deleted.
A second CI job imports every engine module and asserts no import from
`editor/` appears in the import tree.

**Why enforcement, not just convention:** Optionality that is only a
convention degrades. A convenience import added to an engine module on
a busy day silently violates the constraint. Automated checks catch it
immediately.

---

### R15 — Every Public API Has a Docstring

**Rule:** Every public method and class in the stable API tier has a
docstring stating: what it does, parameter expectations, return value,
exceptions it can raise, postconditions the caller can depend on.

**Enforcement:** `ruff` or `pydocstyle` configured to flag missing
docstrings on public methods in `pygame_engine/` public modules.

**Why:** A public API without documentation is not a public API — it is
an undocumented internal. Documentation is part of the deliverable.

---

### R16 — Naming Conventions Are Enforced

**Rule:**
- Classes: `PascalCase`, no abbreviations, singular
- Methods and properties: `snake_case`, verbs for actions, nouns for
  properties, booleans prefixed `is_`, `has_`, `can_`, `should_`
- Events: dot-separated, noun-first — `engine.scene.changed`, not
  `on_scene_changed`
- Constants: `UPPER_SNAKE_CASE`
- Files: `snake_case.py`, one primary class per file

**No abbreviations in public identifiers:**
- `screen_width` not `sw`
- `callback` not `cb`
- `colour` not `col` (when meaning colour)
- `button` not `btn`

**Permitted exceptions:** `dt` (delta time — industry standard), `fps`,
`ui` (module name), `x`, `y`, `w`, `h` (standard geometric notation).

**Enforcement:** `ruff` or `pylint` with project-specific config.
Naming violations fail the CI build.

---

### R17 — File Length Has a Soft Limit and Hard Cap

**Rule:**
- Soft limit: 400 lines. Files approaching this should be reviewed for
  decomposition opportunities.
- Hard cap: 600 lines. Files exceeding this require a justification comment
  at the top of the file and a tracking issue. No new features are added
  to a file over the hard cap until it has been decomposed.

**Why:** Long files are a symptom of too much responsibility in one place.
The limit forces decomposition conversations before a file becomes
unmaintainable.

**Current violations in game code:**
- `management_scene.py` (~937 lines) — over hard cap
- `game_hub_scene.py` (~619 lines) — over soft limit
- `inventory_scene.py` (~600 lines) — at hard cap
- Several other scene files over soft limit

These are tracked in Section 8 as required changes.

---

### R18 — Engine Scope: 2D Interactive Applications

**Rule:** pygame_engine is scoped to interactive 2D applications — games,
tools, simulations — where the primary interface is a scene graph of
widgets and entities. Features that belong to this scope are in scope.
Features that belong to other scopes are not refused, they are simply not
the engine's responsibility — integrate external libraries for those needs.

**Recommended external libraries:**
- Physics: pymunk
- Networking: (future consideration)
- 3D: out of scope

---

### R19 — pygame-ce Version Is Pinned

**Rule:** `pyproject.toml` pins a specific pygame-ce version, not a range.
Upgrading is a deliberate act with documented process: update pin, run full
test suite, check changelog for breaking changes, update engine code,
commit pin update with CHANGELOG entry.

**Why:** pygame-ce API changes between versions can break the engine
silently. A specific pin means "we know this engine works with this version."
A range means "we think this probably works."

---

### R20 — Layout Descriptor Is the Only Interface Between Editor and Scene

**Rule:** The editor must not read or write any scene state except through
the layout descriptor and its observable properties. Scene instance
variables are private to the scene.

**Why:** Defines a clean contract. The descriptor is the interface.
Anything outside it is private. The editor doesn't need to know about
`self._selected_hero` — it only needs the structural layout. These are
different concerns.

**Corollary:** Any state the editor needs to observe must be expressed
as an observable property on the layout descriptor, not as a plain
instance variable.

---

## 8. Required Codebase Changes

These are changes to existing code that the restrictions and new design
require. Ordered by priority — items at the top block other work.

---

### Priority 1 — Must Fix Before Building New Features

**[CHANGE-01] Fix Observable[T] — Memory leaks and missing features**

File: `pygame_engine/state/observable.py`

What: The current `Observable[T]` has no weak references, no transaction
batching, and no old-value in event payload.

Impact: Current memory leak. Every scene navigation that involves
subscriptions leaks memory.

Required changes:
- Weak reference subscriptions
- `transaction()` context manager
- `(old_value, new_value)` in subscriber callbacks

Breaking change: subscriber signatures change from `fn(new_value)` to
`fn(old_value, new_value)`. All existing subscribers must be updated.

Tests required: Property-based tests via Hypothesis. Weak reference
cleanup tests. Transaction batching tests. Old-value correctness tests.
These tests must pass before any other feature is built.

---

**[CHANGE-02] Fix theme singleton — No stateful singletons**

File: `pygame_engine/theme/runtime.py`

What: `get_theme()` accesses a module-level singleton. Violates R09.

Impact: Two `Application` instances (tests, editor) share theme state.

Required changes:
- Theme must live on `Application` instance
- Widgets must receive theme through a context, not via global
- Three options (in order of preference):
  1. Pass theme as parameter to `render(surface, theme)` — cleanest,
     breaking change to Widget interface
  2. Store theme on a `RenderContext` object passed to `render()`
  3. Widgets call `app.theme` through a context reference stored at
     construction time

Decision needed before implementation. All three are acceptable.
Option 2 is recommended — `RenderContext` can carry theme, camera,
and other render-time context without polluting the method signature.

---

**[CHANGE-03] Move shared palette to game/ui/**

Files: `game/scenes/management_scene.py` and all scenes that import from it

What: `management_scene.py` is currently used as a shared palette library.
Other scenes import `DESK_BG`, `DeskButton`, `TAB_H`, etc. from it.
Violates R07 (scenes import each other).

Required changes:
```
game/
  ui/
    desk_theme.py     # all palette constants
    desk_button.py    # DeskButton class
  scenes/
    management_scene.py  # no longer a shared library
    inventory_scene.py   # imports from game.ui, not management_scene
    # ... all other scenes
```

Impact: All game scenes require import path updates. No logic changes.

---

**[CHANGE-04] Decompose management_scene.py**

File: `game/scenes/management_scene.py` (~937 lines, over hard cap)

What: Single file over the hard cap. No new features can be added
until decomposed. Violates R17.

Required changes:
```
game/scenes/management/
  __init__.py              # re-exports ManagementScene
  management_scene.py      # scene class — orchestration only
  recruit_list.py          # recruit list rendering and interaction
  roster_list.py           # roster list rendering and interaction
  detail_panel.py          # hero detail panel
  negotiation_panel.py     # negotiation controls and steppers
```

Each file should stay under 400 lines. The scene class becomes an
orchestrator — it holds panels, routes events, calls render.

---

### Priority 2 — Should Fix Before Adding Features to Affected Systems

**[CHANGE-05] Add TimeManager to Application**

Files: `pygame_engine/app/application.py` (new), new `time_manager.py`

What: `dt` is computed inline. No `time_scale`, no `unscaled_delta_time`,
no `frame_count`, no `time`. Editor play/stop requires `time_scale`.

Required changes:
- New `pygame_engine/app/time_manager.py`
- `Application._loop()` computes raw dt, stores in `TimeManager`,
  passes `time_manager.delta_time` to `scene.update()`
- `app.time` property

---

**[CHANGE-06] Add FocusManager to Application**

Files: `pygame_engine/ui/focus/` (existing), new `focus_manager.py`

What: Focus is managed per-Panel. No global focus state. No programmatic
focus. No standardised focus ring.

Required changes:
- New `FocusManager` class
- `app.focus` property
- Focus ring drawn by `FocusManager` as post-render pass
- `Widget.tab_index` and `Widget.focus_trap` fields
- `ui.focus.changed` event on bus

---

**[CHANGE-07] Add SubscriptionGroup and auto-cleanup to Scene**

Files: `pygame_engine/state/observable.py`, `pygame_engine/scene/scene.py`

What: No automatic subscription cleanup when scenes exit.
Current memory leak.

Required changes:
- New `SubscriptionGroup` class
- `Scene.subscriptions: SubscriptionGroup` property
- `Scene.on_exit()` calls `self.subscriptions.dispose()`

Depends on: CHANGE-01 (Observable upgrade)

---

**[CHANGE-08] Add extension hooks to Application**

Files: `pygame_engine/app/application.py`

What: No hook system for optional modules. The editor cannot attach to the
game loop without modifying Application.

Required changes:
- `on_startup`, `on_shutdown`, `on_pre_render`, `on_post_render`, etc.
- Priority parameter on each hook entry

---

**[CHANGE-09] Add `mode` and `reduced_motion` to AppConfig**

Files: `pygame_engine/app/application.py`

What: `debug: bool` is insufficient. Three-way mode needed. No
`reduced_motion` flag.

Required changes:
- `mode: Literal["development", "production", "testing"]`
- `reduced_motion: bool = False`
- All animation systems check `app.reduced_motion`

---

### Priority 3 — Cleanup Tasks (Don't Block New Features)

**[CHANGE-10] Abbreviation cleanup in game render methods**

Files: All `game/scenes/*.py` render methods

What: `sw`, `sh`, `lx`, `rx`, `by`, `col` (ambiguous), etc. throughout
game scene render methods. Violates R16.

Note: `col` is particularly problematic — used for both "colour" (a colour
tuple) and "column" (an x coordinate) in the same files.

Required changes: Mechanical rename. `sw` → `surface_width`, `sh` →
`surface_height`, `col` (colour) → `colour`, `col` (column) → `column_x`.

---

**[CHANGE-11] Docstring coverage for public API**

Files: All public engine widgets and classes

What: Most widgets have class docstrings but no method docstrings.

Required changes: Add docstrings to all public methods in the stable API
tier. Priority: `Observable[T]` first, then `Widget`, `Scene`,
`Application`.

---

**[CHANGE-12] File decomposition for game scenes over soft limit**

Files: `game_hub_scene.py`, `inventory_scene.py`, and others

What: Several scene files are between soft limit (400) and hard cap (600).
No immediate block but should be addressed.

---

**[CHANGE-13] Scene registry via @register_scene decorator**

Files: New `game/scenes/registry.py`

What: `TabBar` navigation currently uses lazy imports of scene classes.
Should use a scene registry for clean decoupling.

Required changes:
- `@register_scene` decorator
- `scene_registry.get(name: str) -> type[Scene]`
- Update `TabBar._navigate()` to use registry

---

**[CHANGE-14] Atomic writes in SaveManager**

Files: `pygame_engine/persistence/`

What: Current save writes may be interruptible. Should write to temp file
then rename.

---

**[CHANGE-15] Add `widget_id` field to Widget**

Files: `pygame_engine/ui/base/widget.py`

What: No stable identifier for editor selection. `id(widget)` changes
on recreation.

Required changes:
- `widget_id: str | None = None` field on `Widget`
- No other changes — purely additive

---

## 9. Implementation Order

This section specifies the recommended sequence for all planned work.
Each phase must be complete — code, tests, and documentation — before
the next phase begins.

---

### Phase A — Foundation Repairs (Prerequisite for Everything)

These fix current bugs and violations. Nothing else should be built until
these are done.

| ID | Task | Priority reason |
|---|---|---|
| CHANGE-01 | Observable[T] upgrade (weak refs, batching, old-value) | Current memory leak. Everything builds on this. |
| CHANGE-09 | Add `mode` and `reduced_motion` to AppConfig | Needed before error handling and editor |
| CHANGE-02 | Fix theme singleton | Current architectural violation. Affects all widget rendering. |
| CHANGE-07 | SubscriptionGroup + Scene auto-cleanup | Current memory leak. Depends on CHANGE-01. |

**Gate:** Full test suite passes. Property-based Observable tests pass.
No memory leaks detectable in leak tests.

---

### Phase B — Core Additions

New engine capabilities that everything else depends on.

| ID | Task | Priority reason |
|---|---|---|
| CHANGE-05 | TimeManager | Required for editor play/stop, pause menus, slow-motion |
| CHANGE-08 | Extension hooks on Application | Required for editor to attach without modifying Application |
| CHANGE-15 | `widget_id` field on Widget | Required for editor selection system |
| CHANGE-06 | FocusManager | Centralised focus, required for accessibility and editor |
| CHANGE-14 | Atomic saves in SaveManager | Correctness fix |

**Gate:** All existing tests pass. New tests for each addition pass.

---

### Phase C — Game Codebase Repairs

Fix violations in the game code before building new game features.

| ID | Task | Priority reason |
|---|---|---|
| CHANGE-03 | Move shared palette to game/ui/ | Removes scene-to-scene imports |
| CHANGE-04 | Decompose management_scene.py | Required by hard cap restriction |
| CHANGE-13 | @register_scene and scene registry | Clean navigation, removes lazy import pattern |
| CHANGE-10 | Abbreviation cleanup | Naming convention compliance |
| CHANGE-11 | Docstring coverage | Public API documentation requirement |
| CHANGE-12 | Decompose other long scene files | Soft limit compliance |

---

### Phase D — Engine Modules: Layout and Editor Foundation

| Task | Depends on |
|---|---|
| `ObservableRect` class | CHANGE-01 |
| `DescribedScene` base class | `ObservableRect`, CHANGE-07 |
| `SceneDescriptor` and `WidgetNode` | `ObservableRect` |
| Layout DSL (`L.panel()`, `L.dynamic()`) | `SceneDescriptor` |
| `LayoutLoader` — JSON read/write | `SceneDescriptor` |
| Migrate one game scene to `DescribedScene` as proof of concept | All above |

---

### Phase E — Engine Modules: Debug and Testing Infrastructure

| Task | Depends on |
|---|---|
| `GizmoRenderer` | CHANGE-08 (hooks) |
| `SceneTestHarness` | Phase B complete |
| `TimeManager.register_fixed_step()` | CHANGE-05 |
| `preload()` lifecycle method | CHANGE-08 |
| Error handling — `ErrorScene`, three categories | CHANGE-09 |
| Remote debug server | CHANGE-08 |

---

### Phase F — Engine Modules: Editor

| Task | Depends on |
|---|---|
| Editor shell — ImGui + pygame viewport | Phase D, Phase E |
| Hierarchy panel | Editor shell |
| Inspector panel — read-only first | Editor shell |
| Gizmo overlay in viewport | `GizmoRenderer` |
| Selection system — click to select | Hierarchy + gizmos |
| Move gizmo — drag to move | Selection |
| Resize gizmo — handle drag | Selection |
| Inspector — editable fields | `ObservableRect` two-way binding |
| Undo/redo command stack | Move + resize gizmos |
| Play/stop button | CHANGE-05 (TimeManager) |
| Auto-save on change | `LayoutLoader` |
| Grid snap | Move gizmo |
| Event log panel | CHANGE-08 |

---

### Phase G — Engine Modules: Audio and Input

| Task | Depends on |
|---|---|
| Audio bus topology | CHANGE-05 (time_scale integration) |
| `MusicPlayer` — crossfade | Audio buses |
| `InputRecorder` | CHANGE-08 |
| `AudioSnapshot` | Audio buses |

---

### Phase H — Game: Remaining Scenes and Features

Continue hero management game development using the repaired and extended
engine. All new game scenes use `DescribedScene`. All new game scenes
register with `@register_scene`.

---

### Phase I — Polish and Deferred Features

| Task | Notes |
|---|---|
| Anchor system in `WidgetNode` | When responsive layout is needed |
| Prefab instance overrides | When prefab editing is needed |
| Multi-selection in editor | Phase 2 editor feature |
| Alignment and distribution tools | Phase 2 editor feature |
| `SceneTestHarness` expansion | As game test coverage grows |

---

## 10. Open Questions

Decisions not yet made that will need answers during implementation.

**Theme access pattern after singleton removal**

Three options stated in CHANGE-02. Which one? Recommendation is
`RenderContext` passed to `render()`. Needs explicit decision before
CHANGE-02 begins.

**`Observable[T]` subscriber signature change**

Breaking change to `fn(new_value)` → `fn(old_value, new_value)`.
Need to audit all current subscribers and update them as part of CHANGE-01.
Some subscribers may not need the old value — they can ignore the first
parameter. Confirm this is the chosen approach.

**`DescribedScene` and `HeroScene` relationship**

Current hierarchy: `Scene → HeroScene → ManagementScene` (depth 3, at limit).
With `DescribedScene`: `Scene → DescribedScene → ManagementScene` — would
`HeroScene` still be needed? Or does `HeroScene`'s shared utilities move
into a composed helper class?

**Scene registry implementation**

Should `@register_scene` be in the engine or in the game? It references
the scene class — which is game code — but the registry pattern itself is
engine infrastructure. Recommendation: engine provides the registry
mechanism, game code uses the decorator. Confirm.

**Audio streaming implementation**

Does pygame-ce support streaming audio natively, or does this require a
separate implementation? Confirm capability before designing the API.

**`preload()` threading model**

If `preload()` loads assets on a background thread, how is the completion
signal communicated to the main thread without violating R13? Options:
thread-safe queue checked each frame, or cooperative loading spread across
frames (no threading). Confirm approach before implementing `preload()`.
