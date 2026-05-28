"""
GizmoRenderer — debug visualisation overlay for development mode.

Gizmos draw visual helpers (bounding boxes, collision shapes, camera
bounds, pathfinding grids, selection handles) on top of the game world.
They are visible in development mode and completely absent in production —
``app.gizmos`` returns ``None`` in production, making every gizmo call
a single ``None`` check away from zero cost.

Usage (in a scene)::

    def render(self, surface, ctx):
        super().render(surface, ctx)
        if app.gizmos:
            app.gizmos.draw_rect(self._player.rect, (0, 255, 0),
                                 label="player", category="bounds")
            app.gizmos.draw_circle(self._enemy.pos, 40, (255, 0, 0),
                                   label="aggro radius", category="ai")

Usage (filter categories)::

    app.gizmos.show_only("bounds", "collision")
    app.gizmos.show_all()
    app.gizmos.hide("ai")

Categories let developers toggle which gizmo types are visible without
touching scene code. Useful when debugging a specific system.

Registration pattern (for complex, per-entity gizmos)::

    class PlayerGizmo:
        def __init__(self, player): self._player = player
        def draw(self, renderer, camera=None): ...

    app.gizmos.register(PlayerGizmo(player))   # on scene enter
    app.gizmos.unregister(player_gizmo)        # on scene exit
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pygame


@runtime_checkable
class Gizmo(Protocol):
    """
    Protocol for objects that draw their own debug visualisation.

    Register with ``app.gizmos.register(gizmo)`` and unregister with
    ``app.gizmos.unregister(gizmo)`` on scene exit.
    """

    def draw(
        self,
        renderer: "GizmoRenderer",
        camera:   object | None = None,
    ) -> None:
        """Draw this gizmo using the provided renderer."""
        ...


class GizmoRenderer:
    """
    Debug drawing system for development and editor modes.

    Owned by ``Application`` when ``config.mode == "development"``.
    ``app.gizmos`` is ``None`` in production — scenes check::

        if app.gizmos:
            app.gizmos.draw_rect(rect, (0, 255, 0))

    All draw calls are issued each frame and cleared after rendering.
    Registered ``Gizmo`` objects are called each frame to issue their
    own draw calls.

    Categories
    ----------
    Every draw call accepts an optional ``category`` string. Use this to
    group related gizmos so they can be toggled together::

        app.gizmos.draw_rect(rect, GREEN, category="bounds")
        app.gizmos.draw_rect(hitbox, RED,  category="collision")
        app.gizmos.hide("bounds")   # only collision gizmos visible
    """

    _DEFAULT_COLOUR = (0, 255, 0)

    def __init__(self) -> None:
        self._enabled:    bool           = True
        self._hidden:     set[str]       = set()
        self._gizmos:     list[Gizmo]    = []
        # Queued draw calls: list of (fn, args, kwargs, category)
        self._queue: list[tuple] = []

    # ── Category control ──────────────────────────────────────────────────────

    def hide(self, *categories: str) -> None:
        """Hide all gizmos belonging to the given categories."""
        self._hidden.update(categories)

    def show(self, *categories: str) -> None:
        """Show (un-hide) gizmos belonging to the given categories."""
        self._hidden.difference_update(categories)

    def show_all(self) -> None:
        """Make all categories visible."""
        self._hidden.clear()

    def show_only(self, *categories: str) -> None:
        """Hide everything except the named categories.

        Args:
            *categories: Category names to keep visible.
        """
        # We don't know all possible categories until draw calls happen,
        # so we invert: mark a special "show_only" mode.
        # Simplest approach: clear hidden, then re-populate after first frame.
        # For now: set a whitelist flag.
        self._whitelist: set[str] | None = set(categories)

    @property
    def enabled(self) -> bool:
        """Whether gizmo rendering is currently active."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def _category_visible(self, category: str) -> bool:
        """Return True if the category should be drawn this frame."""
        whitelist = getattr(self, "_whitelist", None)
        if whitelist is not None:
            return category in whitelist
        return category not in self._hidden

    # ── Draw primitives ───────────────────────────────────────────────────────

    def draw_rect(
        self,
        rect:     pygame.Rect,
        colour:   tuple = _DEFAULT_COLOUR,
        label:    str | None = None,
        width:    int = 1,
        dashed:   bool = False,
        category: str = "default",
    ) -> None:
        """
        Draw a rectangle outline.

        Args:
            rect:     The rectangle to draw (in screen coordinates).
            colour:   RGB or RGBA colour tuple.
            label:    Optional text label drawn at the top-left corner.
            width:    Line width in pixels.
            dashed:   If True, draw as a dashed outline (approximate).
            category: Gizmo category for filtering.
        """
        self._queue.append(("rect", rect.copy(), colour, label, width, dashed, category))

    def draw_circle(
        self,
        pos:      tuple[float, float],
        radius:   float,
        colour:   tuple = _DEFAULT_COLOUR,
        label:    str | None = None,
        width:    int = 1,
        category: str = "default",
    ) -> None:
        """
        Draw a circle outline.

        Args:
            pos:      Centre position in screen coordinates.
            radius:   Radius in pixels.
            colour:   RGB or RGBA colour tuple.
            label:    Optional label drawn near the circle.
            width:    Line width. 0 = filled.
            category: Gizmo category for filtering.
        """
        self._queue.append(("circle", pos, radius, colour, label, width, category))

    def draw_line(
        self,
        start:    tuple[float, float],
        end:      tuple[float, float],
        colour:   tuple = _DEFAULT_COLOUR,
        width:    int = 1,
        category: str = "default",
    ) -> None:
        """
        Draw a line segment.

        Args:
            start:    Start position in screen coordinates.
            end:      End position in screen coordinates.
            colour:   RGB or RGBA colour tuple.
            width:    Line width in pixels.
            category: Gizmo category for filtering.
        """
        self._queue.append(("line", start, end, colour, width, category))

    def draw_arrow(
        self,
        start:    tuple[float, float],
        end:      tuple[float, float],
        colour:   tuple = _DEFAULT_COLOUR,
        width:    int = 1,
        category: str = "default",
    ) -> None:
        """
        Draw a line with an arrowhead at the end point.

        Args:
            start:    Tail position in screen coordinates.
            end:      Head (arrowhead) position in screen coordinates.
            colour:   RGB or RGBA colour tuple.
            width:    Line width in pixels.
            category: Gizmo category for filtering.
        """
        self._queue.append(("arrow", start, end, colour, width, category))

    def draw_text(
        self,
        pos:      tuple[float, float],
        text:     str,
        colour:   tuple = _DEFAULT_COLOUR,
        category: str = "default",
    ) -> None:
        """
        Draw a text label at the given screen position.

        Args:
            pos:      Top-left position in screen coordinates.
            text:     The string to render.
            colour:   RGB or RGBA colour tuple.
            category: Gizmo category for filtering.
        """
        self._queue.append(("text", pos, text, colour, category))

    def draw_cross(
        self,
        pos:      tuple[float, float],
        size:     int = 8,
        colour:   tuple = _DEFAULT_COLOUR,
        category: str = "default",
    ) -> None:
        """
        Draw a small cross/plus marker at the given position.

        Args:
            pos:      Centre position in screen coordinates.
            size:     Half-length of each arm in pixels.
            colour:   RGB or RGBA colour tuple.
            category: Gizmo category for filtering.
        """
        x, y = int(pos[0]), int(pos[1])
        self.draw_line((x - size, y), (x + size, y), colour, category=category)
        self.draw_line((x, y - size), (x, y + size), colour, category=category)

    def draw_grid(
        self,
        bounds:    pygame.Rect,
        cell_size: int = 32,
        colour:    tuple = (60, 60, 80),
        category:  str = "grid",
    ) -> None:
        """
        Draw a grid overlay within the given bounds.

        Args:
            bounds:    Area to cover with grid lines (screen coordinates).
            cell_size: Size of each grid cell in pixels.
            colour:    RGB or RGBA colour tuple.
            category:  Gizmo category for filtering.
        """
        x = bounds.left
        while x <= bounds.right:
            self.draw_line((x, bounds.top), (x, bounds.bottom),
                           colour, category=category)
            x += cell_size
        y = bounds.top
        while y <= bounds.bottom:
            self.draw_line((bounds.left, y), (bounds.right, y),
                           colour, category=category)
            y += cell_size

    # ── Gizmo object registration ─────────────────────────────────────────────

    def register(self, gizmo: Gizmo) -> None:
        """
        Register a ``Gizmo`` object for per-frame drawing.

        ``gizmo.draw(renderer, camera)`` is called each frame during the
        gizmo render pass. Unregister on scene exit to avoid stale references.

        Args:
            gizmo: An object implementing the ``Gizmo`` protocol.
        """
        if gizmo not in self._gizmos:
            self._gizmos.append(gizmo)

    def unregister(self, gizmo: Gizmo) -> None:
        """
        Remove a registered gizmo object.

        No-op if the gizmo was not registered.

        Args:
            gizmo: The gizmo to remove.
        """
        try:
            self._gizmos.remove(gizmo)
        except ValueError:
            pass

    def clear_gizmos(self) -> None:
        """Unregister all gizmo objects."""
        self._gizmos.clear()

    # ── Frame rendering ───────────────────────────────────────────────────────

    def render(
        self,
        surface: pygame.Surface,
        camera:  object | None = None,
    ) -> None:
        """
        Execute all queued draw calls and invoke registered gizmo objects.

        Called once per frame by ``Application._loop()`` as a post-render
        pass via the extension hook system. Queue is cleared after rendering.

        Args:
            surface: The display surface to draw onto.
            camera:  Optional camera object passed to registered gizmos
                     so they can convert world → screen coordinates.
        """
        if not self._enabled:
            self._queue.clear()
            return

        # Registered gizmos issue their draw calls first
        for gizmo in list(self._gizmos):
            try:
                gizmo.draw(self, camera)
            except Exception:
                pass  # never let a bad gizmo crash the frame

        font = self._get_label_font()

        for call in self._queue:
            kind = call[0]
            cat  = call[-1]
            if not self._category_visible(cat):
                continue
            self._execute(surface, call, font)

        self._queue.clear()

    def _execute(
        self,
        surface: pygame.Surface,
        call:    tuple,
        font:    pygame.font.Font | None,
    ) -> None:
        """Execute a single queued draw call."""
        kind = call[0]

        if kind == "rect":
            _, rect, colour, label, width, dashed, _ = call
            if dashed:
                self._draw_dashed_rect(surface, colour, rect, width)
            else:
                pygame.draw.rect(surface, colour, rect, width)
            if label and font:
                surf = font.render(label, True, colour)
                surface.blit(surf, (rect.x + 2, rect.y - 14))

        elif kind == "circle":
            _, pos, radius, colour, label, width, _ = call
            pygame.draw.circle(surface, colour,
                               (int(pos[0]), int(pos[1])), int(radius), width)
            if label and font:
                surf = font.render(label, True, colour)
                surface.blit(surf, (int(pos[0]) + int(radius) + 2, int(pos[1]) - 7))

        elif kind == "line":
            _, start, end, colour, width, _ = call
            pygame.draw.line(
                surface, colour,
                (int(start[0]), int(start[1])),
                (int(end[0]), int(end[1])),
                width,
            )

        elif kind == "arrow":
            _, start, end, colour, width, _ = call
            sx, sy = int(start[0]), int(start[1])
            ex, ey = int(end[0]),   int(end[1])
            pygame.draw.line(surface, colour, (sx, sy), (ex, ey), width)
            # Simple arrowhead: two short lines
            import math
            angle = math.atan2(ey - sy, ex - sx)
            arrow_len = 10
            for side in (+0.4, -0.4):
                ax = ex - int(arrow_len * math.cos(angle + side))
                ay = ey - int(arrow_len * math.sin(angle + side))
                pygame.draw.line(surface, colour, (ex, ey), (ax, ay), width)

        elif kind == "text":
            _, pos, text, colour, _ = call
            if font:
                surf = font.render(text, True, colour)
                surface.blit(surf, (int(pos[0]), int(pos[1])))

    def _draw_dashed_rect(
        self,
        surface: pygame.Surface,
        colour:  tuple,
        rect:    pygame.Rect,
        width:   int,
        dash:    int = 6,
    ) -> None:
        """Draw a dashed rectangle outline."""
        def dashed_line(s, c, p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            dx, dy  = x2 - x1, y2 - y1
            length  = max(abs(dx), abs(dy))
            if length == 0:
                return
            steps = max(1, length // (dash * 2))
            for i in range(steps):
                t0 = i / steps
                t1 = (i + 0.5) / steps
                ax = int(x1 + dx * t0); ay = int(y1 + dy * t0)
                bx = int(x1 + dx * t1); by = int(y1 + dy * t1)
                pygame.draw.line(s, c, (ax, ay), (bx, by), width)

        dashed_line(surface, colour, rect.topleft,     rect.topright)
        dashed_line(surface, colour, rect.topright,    rect.bottomright)
        dashed_line(surface, colour, rect.bottomright, rect.bottomleft)
        dashed_line(surface, colour, rect.bottomleft,  rect.topleft)

    _label_font: pygame.font.Font | None = None

    def _get_label_font(self) -> pygame.font.Font | None:
        """Lazy-initialise the label font (requires pygame.font.init())."""
        if GizmoRenderer._label_font is None:
            try:
                pygame.font.init()
                GizmoRenderer._label_font = pygame.font.SysFont("monospace", 11)
            except Exception:
                pass
        return GizmoRenderer._label_font

    def __repr__(self) -> str:
        return (
            f"GizmoRenderer(enabled={self._enabled}, "
            f"gizmos={len(self._gizmos)}, "
            f"queued={len(self._queue)})"
        )
