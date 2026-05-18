"""
Unlike the stateless ``anchor()`` function, ``AnchorLayout`` remembers
the rules for each widget so it can recompute all positions when the
window resizes.

Usage::

    from pygame_engine.layout.anchor_layout import AnchorLayout

    layout = AnchorLayout()
    layout.add(btn_menu,  point="top_left",     size=(120, 40), margin=16)
    layout.add(lbl_score, point="top_right",    size=(140, 40), margin=16)
    layout.add(hud_bar,   point="bottom",       size=(400, 32), margin=16)
    layout.add(crosshair, point="center",       size=(24, 24))
    layout.apply(screen_rect)

    # In on_resize:
    def on_resize(self, width, height):
        self._layout.apply(pygame.Rect(0, 0, width, height))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pygame

from pygame_engine.layout.anchor import ANCHOR_POINTS, anchor


class _HasSetRect(Protocol):
    def set_rect(self, rect: pygame.Rect) -> None: ...


@dataclass
class _AnchorRule:
    widget: _HasSetRect
    point:  str
    size:   tuple[int, int] | None    # None = use widget's current size
    margin: int
    offset: tuple[int, int]


class AnchorLayout:
    """
    Manages a set of anchor rules and reapplies them on resize.

    Each rule pins one widget to an anchor point within the bounds rect.
    Call ``apply(bounds)`` once to set initial positions and again in
    ``Scene.on_resize()`` to update.

    Args:
        bounds: Optional initial bounds rect. If provided, ``apply()``
                is called immediately with these bounds.
    """

    def __init__(self, bounds: pygame.Rect | None = None) -> None:
        self._rules: list[_AnchorRule] = []
        self._last_bounds: pygame.Rect | None = None
        if bounds is not None:
            self._last_bounds = pygame.Rect(bounds)

    def add(
        self,
        widget: _HasSetRect,
        point:  str,
        size:   tuple[int, int] | None = None,
        margin: int                    = 0,
        offset: tuple[int, int]        = (0, 0),
    ) -> "AnchorLayout":
        """
        Register a widget with an anchor rule.

        Args:
            widget: Any object with a ``set_rect(rect)`` method.
            point:  One of the nine anchor point names:
                    ``"top_left"``, ``"top"``, ``"top_right"``,
                    ``"left"``,    ``"center"``, ``"right"``,
                    ``"bottom_left"``, ``"bottom"``, ``"bottom_right"``.
            size:   (width, height) for this widget. If None, the widget's
                    current ``rect.size`` is used (the widget must have a
                    ``rect`` attribute).
            margin: Inset from the nearest edge in pixels.
            offset: Additional (dx, dy) nudge applied after placement.

        Returns:
            self — for chaining.

        Raises:
            ValueError: If ``point`` is not a valid anchor point name.
        """
        if point not in ANCHOR_POINTS:
            raise ValueError(
                f"Unknown anchor point {point!r}. "
                f"Valid points: {sorted(ANCHOR_POINTS)}"
            )
        self._rules.append(_AnchorRule(widget, point, size, margin, offset))
        return self

    def apply(self, bounds: pygame.Rect) -> list[pygame.Rect]:
        """
        Compute and apply rects for all registered widgets.

        Call in ``on_enter`` for initial layout and in ``on_resize``
        to update after a window resize.

        Args:
            bounds: The reference rect — typically ``app.screen_rect``
                    or a sub-region.

        Returns:
            List of computed rects in registration order.
        """
        self._last_bounds = pygame.Rect(bounds)
        rects: list[pygame.Rect] = []

        for rule in self._rules:
            size = rule.size
            if size is None:
                # Fall back to the widget's current size
                widget_rect = getattr(rule.widget, "rect", None)
                if widget_rect is not None:
                    size = (widget_rect.width, widget_rect.height)
                else:
                    size = (0, 0)

            rect = anchor(bounds, size, rule.point, rule.margin, rule.offset)
            rule.widget.set_rect(rect)
            rects.append(rect)

        return rects

    def reapply(self) -> list[pygame.Rect]:
        """
        Re-run layout with the last bounds. No-op if ``apply`` was never called.

        Returns:
            List of computed rects, or empty list if no bounds recorded.
        """
        if self._last_bounds is not None:
            return self.apply(self._last_bounds)
        return []

    def remove(self, widget: _HasSetRect) -> bool:
        """
        Remove a widget's anchor rule.

        Args:
            widget: The widget to remove.

        Returns:
            True if found and removed, False if not registered.
        """
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.widget is not widget]
        return len(self._rules) < before

    def clear(self) -> None:
        """Remove all anchor rules."""
        self._rules.clear()

    @property
    def rule_count(self) -> int:
        """Number of registered anchor rules."""
        return len(self._rules)

    def __repr__(self) -> str:
        return f"AnchorLayout({len(self._rules)} rules)"