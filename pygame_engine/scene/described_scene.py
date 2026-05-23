"""
DescribedScene — the Scene base class for scenes whose UI is authored as a
``SceneDescriptor``.

Source-of-truth model
---------------------
A ``DescribedScene`` does not build widgets directly. It declares its UI as
data — a ``SceneDescriptor`` — and the engine realises that data into a live
widget tree. The descriptor is the single source of truth for layout
(see docs/accepted_decisions.md / the descriptor-authority sprint).

The lifecycle::

    set_screen_rect(rect)    caller supplies the screen size
    on_enter()
      ├─ _build_layout()     subclass populates self.layout (the descriptor)
      ├─ LayoutLoader.load() engine builds the real widget tree from it
      ├─ self.root_widget    set to the built tree — base Scene renders it
      └─ _bind_behavior()    subclass attaches callbacks by widget_id

    on_resize(w, h)
      └─ _rebuild_layout()   re-runs the chain against the new screen size

    on_exit()
      └─ the loaded layout's rect subscriptions are released

Because the base ``Scene`` already delegates ``handle_event`` / ``update`` /
``render`` to ``root_widget``, a ``DescribedScene`` gets event routing,
updates, and rendering for free once the tree is built.

Screen size and resize
----------------------
Layout helpers (``anchor``, ``column``, ``flex``) compute rects against a
screen rect. ``_build_layout()`` reads that rect from ``self.screen_rect``.
Whoever creates the scene must call ``set_screen_rect()`` before
``on_enter()`` — the running app passes ``app.screen_rect``; the editor
passes its viewport size.

``_build_layout()`` is required to be **re-runnable**: it is called once on
enter and again on every ``on_resize()``. It must therefore clear the
descriptor first and read ``self.screen_rect`` fresh each time. The base
class enforces the clear (see ``_run_build_layout``), so a subclass simply
populates a fresh descriptor each call.

Layout vs behaviour
-------------------
The descriptor carries structure and geometry only — it stays
JSON-serialisable, so it cannot hold callables. Behaviour (a Button's
``on_click``, navigation) is attached in ``_bind_behavior()``, *after* the
widgets exist, by looking them up via ``widget_id``.

What a subclass overrides
-------------------------
- ``_build_layout()`` — required. Populate ``self.layout`` against
  ``self.screen_rect``. Must be safe to call repeatedly.
- ``_bind_behavior()`` — optional. Attach callbacks to widgets by id.
- ``editor_context()`` — optional classmethod. Mock data for editor preview.

Example::

    from pygame_engine.scene.described_scene import DescribedScene
    from pygame_engine.layout import anchor

    class MainMenuScene(DescribedScene):

        def _build_layout(self) -> None:
            screen = self.screen_rect
            panel  = anchor(screen, (280, 240), "center")
            with self.layout.builder() as L:
                L.panel("root", x=panel.x, y=panel.y, w=panel.w, h=panel.h)
                L.button("play_btn", x=panel.x + 8, y=panel.y + 8,
                         w=200, h=48, parent="root", label="Play")

        def _bind_behavior(self) -> None:
            self.widget("play_btn").on_click = self._on_play
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pygame

from pygame_engine.scene.scene import Scene
from pygame_engine.scene.scene_descriptor import SceneDescriptor
from pygame_engine.scene.layout_loader import LayoutLoader, LoadedLayout

if TYPE_CHECKING:
    from pathlib import Path
    from pygame_engine.ui.base.widget import Widget


#: Fallback screen size used when a scene is entered before
#: ``set_screen_rect()`` is called. Keeps a misconfigured caller from
#: crashing in ``_build_layout()``; a warning is printed so it is noticed.
_DEFAULT_SCREEN_SIZE = (1280, 720)


class DescribedScene(Scene):
    """
    Scene base class whose UI is authored as a ``SceneDescriptor``.

    Subclasses populate the descriptor in ``_build_layout()``; the engine
    builds the live widget tree from it and assigns ``root_widget``.
    Subclasses then attach behaviour in ``_bind_behavior()``.

    Scenes that do not want descriptor-driven UI should subclass ``Scene``
    directly.
    """

    #: Optional path to a JSON layout file. A subclass may use this in
    #: ``_build_layout()`` via
    #: ``self.layout.load_or_default(self.layout_path, self._default_layout)``.
    layout_path: "Path | None" = None

    def __init__(self) -> None:
        """
        Initialise the scene and create an empty layout descriptor.

        Subclasses that define their own ``__init__`` must call
        ``super().__init__()``.
        """
        super().__init__()
        self.layout: SceneDescriptor = SceneDescriptor()

        #: The screen rect layout helpers compute against. Set via
        #: ``set_screen_rect()`` before ``on_enter()``; refreshed on resize.
        self._screen_rect: pygame.Rect = pygame.Rect(
            0, 0, *_DEFAULT_SCREEN_SIZE)

        #: The realised layout — set in ``on_enter()`` once the widget tree
        #: has been built. ``None`` before that and after ``on_exit()``.
        self._loaded: LoadedLayout | None = None

    # ── Screen size ───────────────────────────────────────────────────────────

    @property
    def screen_rect(self) -> pygame.Rect:
        """
        The screen rect ``_build_layout()`` computes layout against.

        Returns a copy, so reading it cannot accidentally mutate the stored
        value. Set it with ``set_screen_rect()``.
        """
        return pygame.Rect(self._screen_rect)

    def set_screen_rect(self, rect: pygame.Rect) -> None:
        """
        Set the screen rect used for layout.

        Call this before ``on_enter()``. The running application passes
        ``app.screen_rect``; the editor passes its viewport size.

        Does not rebuild anything on its own — ``on_enter()`` and
        ``on_resize()`` drive the build. Setting it after the scene is live
        only takes effect on the next rebuild.

        Args:
            rect: The new screen rect.
        """
        self._screen_rect = pygame.Rect(rect)

    # ── Editor API ────────────────────────────────────────────────────────────

    @classmethod
    def editor_context(cls) -> dict[str, Any]:
        """
        Return mock data for the editor to use when previewing this scene.

        Override to provide representative placeholder values so the scene
        renders meaningfully in the editor without real game state.

        Default: an empty dict.
        """
        return {}

    # ── Layout lifecycle ──────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """
        Populate ``self.layout`` with the scene's widget descriptor tree.

        Required override. Declare the UI here, computing geometry against
        ``self.screen_rect``. Typically uses the ``layout_builder`` DSL
        (``with self.layout.builder() as L: ...``) or
        ``self.layout.load_or_default(self.layout_path, ...)``.

        **Must be re-runnable.** It is called on enter and again on every
        resize. The base class clears the descriptor before each call (see
        ``_run_build_layout``), so a subclass just populates a fresh tree —
        but it must read ``self.screen_rect`` fresh each call rather than
        capturing it once.

        Default: raises, because a ``DescribedScene`` with no layout is
        almost always a mistake. A scene that genuinely wants an empty UI
        can override this with an explicit ``pass``.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must override _build_layout() to "
            f"populate its descriptor. For a deliberately empty scene, "
            f"override it with an explicit 'pass'."
        )

    def _bind_behavior(self) -> None:
        """
        Attach behaviour to the built widgets.

        Optional override. Runs after the widget tree exists — and again
        after every rebuild — so widgets can be looked up by id and wired::

            def _bind_behavior(self) -> None:
                self.widget("play_btn").on_click = self._on_play

        Default: no-op — a purely static scene needs no behaviour.
        """

    def on_enter(self) -> None:
        """
        Build the descriptor, realise it into widgets, and bind behaviour.

        Subclasses overriding ``on_enter()`` must call ``super().on_enter()``.
        """
        self._build_and_load()
        super().on_enter()

    def on_resize(self, width: int, height: int) -> None:
        """
        Rebuild the layout for a new window size.

        Refreshes ``screen_rect`` and re-runs the full build chain so
        ``_build_layout()`` recomputes its anchor-based geometry against the
        new size. Subclasses overriding ``on_resize()`` must call
        ``super().on_resize(width, height)``.

        Args:
            width:  New window width in pixels.
            height: New window height in pixels.
        """
        self.set_screen_rect(pygame.Rect(0, 0, width, height))
        self._rebuild_layout()
        super().on_resize(width, height)

    def on_exit(self) -> None:
        """
        Release the layout's live bindings and clear the descriptor.

        Subclasses overriding ``on_exit()`` must call ``super().on_exit()``.
        """
        self._dispose_loaded()
        self.root_widget = None
        self.layout.clear()
        super().on_exit()

    # ── Build internals ───────────────────────────────────────────────────────

    def _build_and_load(self) -> None:
        """
        Run the full build chain: layout → load → bind.

        Shared by ``on_enter()`` (first build) and ``_rebuild_layout()``
        (every rebuild) so the two paths cannot drift apart.
        """
        self._run_build_layout()

        self._loaded     = LayoutLoader().load(self.layout)
        self.root_widget = self._loaded.root

        self._bind_behavior()

    def _rebuild_layout(self) -> None:
        """
        Tear down the current widget tree and build a fresh one.

        Used by ``on_resize()``. Disposes the old layout's rect
        subscriptions first so they do not leak, then re-runs the build
        chain against the current ``screen_rect``.
        """
        self._dispose_loaded()
        self._build_and_load()

    def _run_build_layout(self) -> None:
        """
        Clear the descriptor, then call the subclass ``_build_layout()``.

        Clearing here — rather than trusting each subclass to remember —
        is what makes ``_build_layout()`` safely re-runnable: a second call
        cannot collide with nodes left over from the first.
        """
        self.layout.clear()
        self._build_layout()

    def _dispose_loaded(self) -> None:
        """Release the current loaded layout's bindings, if any."""
        if self._loaded is not None:
            self._loaded.dispose()
            self._loaded = None

    # ── Widget lookup ─────────────────────────────────────────────────────────

    def widget(self, widget_id: str) -> "Widget":
        """
        Return the built widget with ``widget_id``.

        For use in ``_bind_behavior()`` and scene logic.

        Raises:
            RuntimeError: If called before the widget tree has been built.
            KeyError:     If no widget has that id (raised by the loader).
        """
        if self._loaded is None:
            raise RuntimeError(
                f"{type(self).__name__}.widget({widget_id!r}) called before "
                f"the layout was built. Call it from _bind_behavior() or "
                f"after on_enter(), not from __init__ or _build_layout()."
            )
        return self._loaded.by_id(widget_id)

    def find_widget(self, widget_id: str) -> "Widget | None":
        """
        Return the built widget with ``widget_id``, or ``None``.

        The non-raising counterpart to ``widget()``. Also returns ``None``
        if the layout has not been built yet.
        """
        if self._loaded is None:
            return None
        return self._loaded.find(widget_id)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"nodes={self.layout.node_count}, "
            f"built={self._loaded is not None})"
        )
