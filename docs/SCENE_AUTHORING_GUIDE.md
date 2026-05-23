# pygame_engine — Scene Authoring Guide

**Version:** 2.0-design
**Authority:** Practical supplement to ARCHITECTURE.md. Reflects
accepted decision #25 (Scene Descriptor Is the Source of Truth for UI Layout).

This guide covers how to write a scene in pygame_engine. It bridges the
gap between understanding the architecture and actually writing a scene
— the conventions, patterns, and things every scene should do.

This is not documentation of the engine internals. It is a guide for
developers writing game scenes.

---

## 1. Choosing a Base Class

Two base classes, for two kinds of scene.

### `DescribedScene` — the default for scenes with a UI

Use `DescribedScene` for any scene with a structural layout of engine
widgets — panels, buttons, labels, inputs. The scene declares its UI as a
`SceneDescriptor` (a tree of widget nodes); the engine builds the real
widget tree from it. This is the path that the scene editor understands,
and per decision #25 it is the source of truth for the scene's layout.

Choose `DescribedScene` when:
- The scene is built from engine widgets (`Panel`, `Button`, `Label`, …).
- You want the layout to be editable in the scene editor.
- You want the layout to persist to / load from a `.layout.json` file.

### `Scene` — for custom-rendered or trivial scenes

Use the plain `Scene` base class when a descriptor would not help:
- The scene draws itself with custom `pygame.draw` calls rather than
  composing engine widgets (the skeleton in section 2 is such a scene).
- The scene is a trivial overlay with little or no layout.
- You have a deliberate reason to want zero descriptor involvement.

Both share the same lifecycle and frame methods (sections 3–11 apply to
both). `DescribedScene` is a subclass of `Scene` — it adds descriptor
authoring on top, it does not change the fundamentals.

**Rule of thumb:** a scene made of engine widgets is a `DescribedScene`;
a scene that paints its own pixels is a `Scene`.

---
## 2. The Scene Skeleton

Every scene follows this structure. The order of methods is consistent
across all scenes — this makes them predictable to read.

```python
"""
ManagementScene — guild roster and recruit negotiation.

Displays available recruits on the left and the current roster on the
right. Allows hiring recruits and dismissing heroes via confirmation dialog.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

from pygame_engine.scene import Scene
from pygame_engine.scene import SlideTransition
from pygame_engine.graphics.text_utils import truncate

from game.ui.desk_theme import (
    DESK_BG, PARCH_BG, PARCH_BORDER, PARCH_TITLE,
    PARCH_TEXT, PARCH_MUTED, P_PAD, P_RAD, TITLE_H, TAB_H,
)
from game.ui.desk_button import DeskButton
from game.scenes._shared_tab_bar import TabBar

if TYPE_CHECKING:
    from pygame_engine.app import Application
    from core.game_state import GameState


class ManagementScene(Scene):
    """Guild management — recruit hiring and hero dismissal."""

    # ── Construction ──────────────────────────────────────────────────────

    def __init__(
        self,
        app:       "Application",
        state:     "GameState",
        on_return: callable,
    ) -> None:
        super().__init__()
        self._app       = app
        self._state     = state
        self._on_return = on_return

        # Interaction state — what the player has selected or is acting on.
        # These are None until the player interacts with the scene.
        self._selected_recruit: object | None = None
        self._selected_hero:    object | None = None
        self._hov_recruit:      object | None = None

        # UI state — built in on_enter, used in render and handle_event.
        # Initialised to empty/None so handle_event does not crash before
        # the first render call populates them.
        self._tab_bar:    TabBar | None        = None
        self._action_btns: list[DeskButton]    = []

        # Status message shown above the tab bar.
        self.status_message = "Select a recruit to negotiate."

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def on_enter(self) -> None:
        """Build layout and initialise the tab bar."""
        self._build_layout()
        self._tab_bar = TabBar(
            self._app, self._state, self._on_return, active="Guild"
        )

    def on_exit(self) -> None:
        """Scene cleanup. SubscriptionGroup (if used) disposes automatically."""
        super().on_exit()

    # ── Events ────────────────────────────────────────────────────────────

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        # Tab bar gets first refusal — navigation must work from anywhere.
        if self._tab_bar and self._tab_bar.handle_event(event):
            return True

        if event.type == pygame.MOUSEWHEEL:
            return self._handle_scroll(event)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in self._action_btns:
                if btn.handle_click(event.pos):
                    return True
            return self._handle_click(event.pos)

        return False

    # ── Update ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        # Update hover state every frame from mouse position.
        # Do not read mouse position in render() — update() is the right place.
        mouse = pygame.mouse.get_pos()
        self._hov_recruit = self._recruit_at(mouse)

        # Update button hover state.
        for btn in self._action_btns:
            btn.update(mouse)

        super().update(dt)

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        surface_width  = surface.get_width()
        surface_height = surface.get_height()

        # -- Background ---------------------------------------------------
        surface.fill(DESK_BG)

        # -- Panels -------------------------------------------------------
        self._draw_panel(surface, self._rect_recruits, "Available Recruits")
        self._draw_panel(surface, self._rect_roster,   "Current Roster")
        self._draw_panel(surface, self._rect_detail,   "Hero Detail")

        # -- Content ------------------------------------------------------
        self._draw_recruit_list(surface)
        self._draw_roster_list(surface)
        self._draw_detail(surface)
        self._draw_action_btns(surface, surface_width, surface_height)

        # -- Overlays (must be last — renders above everything) -----------
        if self._tab_bar:
            self._tab_bar.draw(surface)
        self._draw_status(surface, surface_height)

        # super().render() draws any modal overlay (ConfirmDialog etc.)
        super().render(surface)

    # ── Layout ────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Compute panel rects from current screen dimensions.

        Called once in on_enter(). If the window is resized, on_enter()
        is not called again — handle resizing in on_resize() instead.
        """
        screen_width  = self._app.screen_rect.width
        screen_height = self._app.screen_rect.height
        content_top   = 52 + 12          # below resource bar + gap
        content_height= screen_height - content_top - TAB_H - 16

        recruit_width = int((screen_width - 24) * 0.56)
        right_width   = screen_width - recruit_width - 24
        detail_height = int(content_height * 0.38)
        roster_height = content_height - detail_height - 8

        self._rect_recruits = pygame.Rect(
            8, content_top, recruit_width, content_height
        )
        self._rect_roster   = pygame.Rect(
            recruit_width + 16, content_top, right_width, roster_height
        )
        self._rect_detail   = pygame.Rect(
            recruit_width + 16, content_top + roster_height + 8,
            right_width, detail_height
        )

        # Row dimensions — used by both draw and hit-test methods.
        # Stored on self so they are in sync.
        self._row_height = 72
        self._row_gap    = 8

    # ── Drawing helpers (private, no side effects beyond drawing) ─────────

    def _draw_panel(
        self,
        surface: pygame.Surface,
        rect:    pygame.Rect,
        title:   str,
    ) -> None:
        """Draw a parchment panel with title bar."""
        pygame.draw.rect(surface, PARCH_BG, rect, border_radius=P_RAD)
        pygame.draw.rect(surface, PARCH_BORDER, rect, 1, border_radius=P_RAD)
        title_rect = pygame.Rect(rect.x, rect.y, rect.width, TITLE_H)
        pygame.draw.rect(
            surface, (50, 44, 34), title_rect,
            border_top_left_radius=P_RAD, border_top_right_radius=P_RAD
        )
        font   = pygame.font.SysFont(None, 22)
        label  = font.render(title.upper(), True, PARCH_TITLE)
        surface.blit(label, label.get_rect(
            centerx=rect.centerx, centery=rect.y + TITLE_H // 2
        ))

    def _draw_status(self, surface: pygame.Surface, screen_height: int) -> None:
        """Draw the status message above the tab bar."""
        if not self.status_message:
            return
        font  = pygame.font.SysFont(None, 20)
        label = font.render(self.status_message, True, (180, 165, 120))
        surface.blit(label, (12, screen_height - TAB_H - 18))

    def _draw_recruit_list(self, surface: pygame.Surface) -> None:
        """Draw the scrollable recruit list in the left panel."""
        ...  # implementation

    def _draw_roster_list(self, surface: pygame.Surface) -> None:
        """Draw the current roster in the right panel."""
        ...

    def _draw_detail(self, surface: pygame.Surface) -> None:
        """Draw the selected hero or recruit detail panel."""
        ...

    def _draw_action_btns(
        self,
        surface:       pygame.Surface,
        screen_width:  int,
        screen_height: int,
    ) -> None:
        """Build and draw context-sensitive action buttons.

        Rebuilds self._action_btns every frame based on current selection
        state. Buttons are ephemeral — do not cache them across frames.
        """
        font = pygame.font.SysFont(None, 22)
        mouse = pygame.mouse.get_pos()
        button_y = screen_height - TAB_H - 46
        buttons: list[DeskButton] = []

        if self._selected_recruit:
            btn = DeskButton(
                (screen_width - 210, button_y, 180, 38),
                "Negotiate",
                self._open_negotiation,
                "primary",
            )
            btn.update(mouse)
            buttons.append(btn)

        for btn in buttons:
            btn.draw(surface, font)

        # Store for handle_event to use this frame.
        # Stale from previous frame — always overwrite.
        self._action_btns = buttons

    # ── Hit testing (pure — no side effects) ──────────────────────────────

    def _recruit_at(self, pos: tuple[int, int]) -> object | None:
        """Return the recruit under pos, or None if outside the list."""
        rect = self._rect_recruits
        if not rect.collidepoint(pos):
            return None
        # ... hit test against row rects
        return None

    # ── Event handlers ────────────────────────────────────────────────────

    def _handle_scroll(self, event: pygame.event.Event) -> bool:
        """Handle mousewheel scroll in the recruit or roster panels."""
        mouse = pygame.mouse.get_pos()
        if self._rect_recruits.collidepoint(mouse):
            self._scroll_recruits = max(
                0, self._scroll_recruits - event.y
            )
            return True
        return False

    def _handle_click(self, pos: tuple[int, int]) -> bool:
        """Handle a click anywhere in the scene."""
        recruit = self._recruit_at(pos)
        if recruit:
            self._selected_recruit = recruit
            self.status_message = f"Selected {recruit.name}."
            return True
        return False

    def _open_negotiation(self) -> None:
        """Open the negotiation panel for the selected recruit."""
        if not self._selected_recruit:
            return
        # ... open negotiation
```

---

## 3. What Goes in __init__

**Store only:** references the scene needs across its lifetime.

```python
# Correct — references and initial state
self._app       = app
self._state     = state
self._on_return = on_return
self._selected  = None          # selection state
self._scroll    = 0             # scroll state
self._tab_bar   = None          # built in on_enter
self._action_btns = []          # rebuilt every frame in render
```

**Do not store** in `__init__`:
- Pygame fonts — `SysFont` cannot be called before `pygame.init()`
  which happens inside `app.run()`. Build fonts in `on_enter()`.
- Computed rects — screen size may not be final at construction time.
  Build in `_build_layout()` called from `on_enter()`.
- Game state subscriptions — subscribe in `on_enter()`, not `__init__`.

---


---

## 4. Lifecycle: `on_enter`, `_build_layout`, `_bind_behavior`

This section differs by base class — read the part that applies.

### Plain `Scene`

`on_enter()` is called once when the scene becomes active. It is the
right place for setup that depends on screen size or game state. A
`_build_layout()` helper is a useful *convention* for separating rect
computation from other setup — you define it and call it yourself:

```python
def on_enter(self) -> None:
    self._build_layout()        # compute panel rects
    self._tab_bar = TabBar(...) # create supporting objects
```

For a plain `Scene`, `_build_layout()` is your own method with no
special meaning to the engine — keep it side-effect free (compute and
store rects, nothing more).

### `DescribedScene`

For a `DescribedScene`, `_build_layout()` is **not** a convention — it is
a required override with a defined contract, and the engine calls it for
you. Do **not** call it yourself from `on_enter()`.

`DescribedScene.on_enter()` runs this chain automatically:

1. `_build_layout()` — you populate `self.layout` (the descriptor).
2. The engine's `LayoutLoader` builds the real widget tree from it.
3. `root_widget` is assigned — the base `Scene` then renders and routes
   to it for free.
4. `_bind_behavior()` — you attach callbacks to widgets by `widget_id`.

So a `DescribedScene` overrides `_build_layout()` and (usually)
`_bind_behavior()`, and typically does **not** override `on_enter()` at
all. If you do override `on_enter()`, call `super().on_enter()`.

`_build_layout()` must:
- Populate `self.layout` using the `layout_builder` DSL
  (`with self.layout.builder() as L: ...`) or
  `self.layout.load_or_default(self.layout_path, ...)`.
- Compute geometry against `self.screen_rect` (set for you before
  `on_enter()` runs).
- Be **re-runnable** — it is called again on every `on_resize()`. The
  base class clears the descriptor before each call, so just populate a
  fresh tree; do not assume it runs only once.

`_build_layout()` must **not**:
- Store callables on the descriptor — the descriptor is data only.
- Attach behaviour — that is `_bind_behavior()`'s job.
- Subscribe to observables, load assets, or modify game state.

Behaviour — `on_click` handlers, navigation — goes in `_bind_behavior()`,
which runs after the widgets exist:

```python
def _bind_behavior(self) -> None:
    self.widget("play_btn").on_click = self._on_play
```

`self.widget(id)` returns the built widget (raises if the id is unknown);
`self.find_widget(id)` returns `None` instead of raising.

---

## 5. on_exit — What Not to Put Here

`on_exit()` is called when the scene is popped. For most scenes the only
thing required is `super().on_exit()`:

```python
def on_exit(self) -> None:
    super().on_exit()
```

`super().on_exit()` disposes `self.subscriptions` automatically. The
`subscriptions` group lives on the base `Scene` class — it is available
to every scene, plain `Scene` and `DescribedScene` alike. A
`DescribedScene` additionally releases its layout's live rect bindings
in `super().on_exit()`.

**Do not put** scene navigation here. Navigation happens in response to
user input, not on exit.

**Do not put** game state saves here. Save explicitly when the action
that requires saving occurs — not as a side effect of exiting a scene.

**Do not** manually unsubscribe observables you registered through
`self.subscriptions` — the group handles that for you.
## 6. Events — The Routing Order

Event routing in `_handle_event_scene` follows a strict order:

```python
def _handle_event_scene(self, event: pygame.event.Event) -> bool:
    # 1. Tab bar — navigation must always work
    if self._tab_bar and self._tab_bar.handle_event(event):
        return True

    # 2. Scroll events
    if event.type == pygame.MOUSEWHEEL:
        return self._handle_scroll(event)

    # 3. Mouse clicks — check buttons before background
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        for btn in self._action_btns:
            if btn.handle_click(event.pos):
                return True
        return self._handle_click(event.pos)

    # 4. Keyboard (if the scene uses keyboard input)
    if event.type == pygame.KEYDOWN:
        return self._handle_key(event)

    return False
```

**Tab bar first, always.** If navigation is broken because another
handler consumed the event, the whole app breaks.

**Buttons before background.** A button click must not also trigger
background selection logic.

**Return True when consumed.** This prevents the engine from routing
the event to the scene below on the stack.

---

## 7. update() — What Belongs Here

`update(dt)` runs every frame before `render()`. Use it for:

- Updating hover state from mouse position
- Updating animation accumulators: `self._t += dt`
- Updating button hover: `btn.update(mouse)`
- Reading game state that may have changed: campaign timers, etc.

**Do not** do rendering or drawing in `update()`.
**Do not** read `pygame.time.get_ticks()` — use the `dt` parameter.
**Do not** modify the widget tree from `update()` — that belongs in
event handlers or `on_enter()`.

---

## 8. render() — The Rules

`render()` must be pure given self's current state (Restriction R10):

- Read from `self._*` only — no side effects
- No `pygame.time.get_ticks()` — use `self._t` updated in `update(dt)`
- No `font.render()` without caching — use the dirty flag pattern
- Section headers for readability in long render methods
- `super().render(surface)` always last — it draws modal overlays

**Action buttons are rebuilt every frame.** Do not cache them across
frames. The pattern in the skeleton above is correct:

```python
def _draw_action_btns(self, surface, screen_width, screen_height):
    buttons = []
    if self._selected_recruit:
        btn = DeskButton(...)
        btn.update(mouse)
        buttons.append(btn)
    for btn in buttons:
        btn.draw(surface, font)
    self._action_btns = buttons  # store for this frame's handle_event
```

---

## 9. Hit Testing

Hit testing — "which item is under the mouse?" — is a common pattern
in scenes with lists. Keep hit tests as pure functions:

```python
def _recruit_at(self, pos: tuple[int, int]) -> object | None:
    """Return the recruit under pos, or None."""
    rect = self._rect_recruits
    clip = pygame.Rect(
        rect.x + 1, rect.y + TITLE_H,
        rect.width - 2, rect.height - TITLE_H - 1
    )
    if not clip.collidepoint(pos):
        return None

    row_y = rect.y + TITLE_H + self._row_gap // 2
    for i, recruit in enumerate(self._state.available_recruits):
        if i < self._scroll_recruits:
            continue
        if row_y + self._row_height > rect.bottom:
            break
        row_rect = pygame.Rect(
            rect.x + P_PAD, row_y,
            rect.width - P_PAD * 2, self._row_height
        )
        if row_rect.collidepoint(pos):
            return recruit
        row_y += self._row_height + self._row_gap

    return None
```

**The same hit test logic used in `render()` for row rects must be
used in `_*_at()`.** If the rects differ, clicks land in the wrong
place. Centralise the row rect calculation if it appears in both places.

---

## 10. Navigation

Use the scene registry — never import scene classes directly:

```python
# Wrong — cross-scene import
from game.scenes.inventory_scene import InventoryScene
self._app.scene_manager.replace_with(InventoryScene(...))

# Correct — registry navigation
# (TabBar handles this automatically for standard tabs)
self._tab_bar.navigate("Inventory")

# Correct — programmatic navigation
from pygame_engine.scene import get_scene
InventoryScene = get_scene("InventoryScene")
self._app.scene_manager.replace_with(
    InventoryScene(self._app, self._state, self._on_return),
    SlideTransition(0.3, "left")
)
```

For scenes without a `TabBar`, or for non-tab navigation (e.g. opening
a detail scene), use `get_scene()` directly.

---

## 11. Saving Game State

Save at the point where the action occurs, not on scene exit:

```python
def _hire_recruit(self) -> None:
    """Hire the selected recruit and save."""
    if not self._selected_recruit:
        return
    result = hire_recruit(self._state, self._selected_recruit)
    self.status_message = result
    # Save immediately after the action — not in on_exit()
    from game.app import HeroManagementApp
    HeroManagementApp.save(self._state)
    self._selected_recruit = None
```

This ensures the save happens at a known good state, not at an
arbitrary point during scene teardown.

---


---

## 12. Writing a DescribedScene

A `DescribedScene` declares its UI as data and lets the engine build the
widget tree. The pattern has three parts: `_build_layout()` declares
structure and geometry, `_bind_behavior()` attaches behaviour, and the
engine does the rest.

### The shape

```python
from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.scene import layout_builder  # noqa: F401  (patches builder())
from pygame_engine.layout import anchor, column


class MainMenuScene(DescribedScene):
    """Main menu — Start / Settings / Quit."""

    def __init__(self, app) -> None:
        super().__init__()
        self._app = app

    # ── Layout — structure and geometry only ─────────────────────────────

    def _build_layout(self) -> None:
        screen = self.screen_rect
        panel  = anchor(screen, (280, 240), "center")
        rects  = column(panel, count=3, item_size=(200, 52), spacing=14)

        with self.layout.builder() as L:
            L.stack("root", x=0, y=0, w=screen.w, h=screen.h)
            L.panel("menu_panel",
                    x=panel.x, y=panel.y, w=panel.w, h=panel.h,
                    parent="root")
            L.button("start_btn",
                     x=rects[0].x, y=rects[0].y, w=rects[0].w, h=rects[0].h,
                     parent="menu_panel", label="Start")
            L.button("settings_btn",
                     x=rects[1].x, y=rects[1].y, w=rects[1].w, h=rects[1].h,
                     parent="menu_panel", label="Settings")
            L.button("quit_btn",
                     x=rects[2].x, y=rects[2].y, w=rects[2].w, h=rects[2].h,
                     parent="menu_panel", label="Quit")

    # ── Behaviour — attached after the widgets exist ─────────────────────

    def _bind_behavior(self) -> None:
        self.widget("start_btn").on_click    = self._on_start
        self.widget("settings_btn").on_click = self._on_settings
        self.widget("quit_btn").on_click     = self._on_quit
```

The scene constructs **no widget directly**. It describes a tree; the
engine's `LayoutLoader` realises it. `MainMenuScene` in `game_template`
is the live reference for this pattern.

### Geometry: compute, then store literals

Layout helpers (`anchor`, `column`, `flex`) are computed inside
`_build_layout()` and their **results** — literal `x/y/w/h` numbers — are
stored on the descriptor nodes. The descriptor stays a flat data model.

Because `_build_layout()` re-runs on `on_resize()` and recomputes those
helpers against the new `self.screen_rect`, the layout re-flows on a
window resize for free.

### The layout / behaviour split

The descriptor must stay JSON-serialisable, so it stores **only**
structure and geometry — no callables. A Button's `on_click` is not a
layout property; it is behaviour. Behaviour is attached in
`_bind_behavior()` by looking widgets up via `widget_id`. This split is
what lets a layout round-trip through a `.layout.json` file unchanged.

### The DSL and the widget registry

`self.layout.builder()` yields a fluent builder with one method per
built-in widget type: `L.stack()`, `L.panel()`, `L.button()`,
`L.label()`, `L.input_field()`, `L.image()`, `L.dynamic()`. For a custom
widget type, use the generic `L.node("MyType", ...)`.

For `L.node("MyType", ...)` to work, `"MyType"` must be registered with
the widget registry (`pygame_engine/ui/widget_registry.py`) — see
`widget_contract.md`. An unregistered type fails loudly when the scene
loads; it is never silently skipped.

### editor_context — design-time data

Override `editor_context()` to give the scene editor representative mock
data, so the scene previews meaningfully without a running game:

```python
@classmethod
def editor_context(cls) -> dict:
    return {"gold": 500, "roster": []}
```
