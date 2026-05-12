"""
layout/_shared.py

Internal shared types and helpers for the layout package.

Not part of the public API. Import from layout modules directly.
"""

from __future__ import annotations

from typing import Literal

Align = Literal["start", "center", "end"]

VALID_ALIGN: frozenset[str] = frozenset({"start", "center", "end"})


def _resolve_align(align: Align, origin: int, available: int, size: int) -> int:
    """
    Resolve an alignment value to a pixel position along one axis.

    Args:
        align:     ``"start"``, ``"center"``, or ``"end"``.
        origin:    The starting coordinate of the available space.
        available: The total size of the available space along this axis.
        size:      The size of the item being placed.

    Returns:
        The pixel coordinate to place the item at.

    Raises:
        ValueError: If ``align`` is not a recognised value.
    """
    if align == "start":
        return origin
    if align == "center":
        return origin + (available - size) // 2
    if align == "end":
        return origin + available - size
    raise ValueError(
        f"Unknown alignment {align!r}. Valid values: {sorted(VALID_ALIGN)}"
    )
