"""
pygame_engine.layout

Layout helpers for positioning widgets.

All helpers are stateless functions: bounds in, list of rects out.

Public API::

    from pygame_engine.layout import row, column, grid, anchor
"""

from pygame_engine.layout.anchor import anchor
from pygame_engine.layout.column import column
from pygame_engine.layout.grid   import grid
from pygame_engine.layout.row    import row

__all__ = ["anchor", "column", "grid", "row"]
