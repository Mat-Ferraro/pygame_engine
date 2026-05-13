"""
pygame_engine.layout

Layout helpers for positioning widgets.

Stateless helpers — bounds in, rects out:

    from pygame_engine.layout import anchor, row, column, grid

Stateful responsive helpers — register widgets once, recompute on resize:

    from pygame_engine.layout import AnchorLayout, FlexRow, FlexColumn
"""

from pygame_engine.layout.anchor import anchor
from pygame_engine.layout.anchor_layout import AnchorLayout
from pygame_engine.layout.column import column
from pygame_engine.layout.flex import FlexColumn, FlexRow
from pygame_engine.layout.grid import grid
from pygame_engine.layout.row import row

__all__ = [
    # Stateless
    "anchor",
    "row",
    "column",
    "grid",
    # Stateful / responsive
    "AnchorLayout",
    "FlexRow",
    "FlexColumn",
]
