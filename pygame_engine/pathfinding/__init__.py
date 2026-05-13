"""
pygame_engine.pathfinding

Grid-based A* pathfinding.

Public API::

    from pygame_engine.pathfinding import ObstacleGrid, Pathfinder

    # Build from a Tilemap
    grid   = ObstacleGrid.from_tilemap(tmap, collision_layer="walls")
    finder = Pathfinder(grid, diagonal=True)
    path   = finder.find((2, 3), (15, 10))  # [(2,3), (3,4), ..., (15,10)]

    # Build manually
    grid = ObstacleGrid(cols=20, rows=15)
    grid.set_obstacle(5, 3, True)
    path = Pathfinder(grid).find((0, 0), (19, 14))
"""

from pygame_engine.pathfinding.pathfinder import ObstacleGrid, Pathfinder

__all__ = ["ObstacleGrid", "Pathfinder"]
