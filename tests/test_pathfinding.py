"""tests/test_pathfinding.py"""
import pytest
from pygame_engine.pathfinding import ObstacleGrid, Pathfinder


def test_grid_dimensions():
    g = ObstacleGrid(10, 8)
    assert g.cols == 10 and g.rows == 8

def test_empty_grid_not_blocked():
    g = ObstacleGrid(5, 5)
    assert g.is_blocked(2, 2) is False

def test_set_obstacle():
    g = ObstacleGrid(5, 5)
    g.set_obstacle(2, 2, True)
    assert g.is_blocked(2, 2) is True

def test_out_of_bounds_is_blocked():
    g = ObstacleGrid(5, 5)
    assert g.is_blocked(-1, 0) is True
    assert g.is_blocked(5, 0)  is True
    assert g.is_blocked(0, 10) is True

def test_set_obstacle_out_of_bounds_raises():
    g = ObstacleGrid(5, 5)
    with pytest.raises(IndexError):
        g.set_obstacle(99, 0, True)

def test_fill_blocked():
    g = ObstacleGrid(3, 3)
    g.fill(True)
    for r in range(3):
        for c in range(3):
            assert g.is_blocked(c, r)

def test_invalid_dimensions_raise():
    with pytest.raises(ValueError):
        ObstacleGrid(0, 5)

def test_find_straight_path():
    g = ObstacleGrid(10, 1)
    f = Pathfinder(g)
    path = f.find((0, 0), (9, 0))
    assert path[0]  == (0, 0)
    assert path[-1] == (9, 0)
    assert len(path) == 10

def test_find_no_path_when_blocked():
    g = ObstacleGrid(5, 1)
    g.fill(False)
    g.set_obstacle(2, 0, True)
    assert Pathfinder(g).find((0, 0), (4, 0)) == []

def test_find_start_equals_goal():
    g = ObstacleGrid(5, 5)
    assert Pathfinder(g).find((2, 2), (2, 2)) == [(2, 2)]

def test_find_blocked_start_returns_empty():
    g = ObstacleGrid(5, 5)
    g.set_obstacle(0, 0, True)
    assert Pathfinder(g).find((0, 0), (4, 4)) == []

def test_find_blocked_goal_returns_empty():
    g = ObstacleGrid(5, 5)
    g.set_obstacle(4, 4, True)
    assert Pathfinder(g).find((0, 0), (4, 4)) == []

def test_find_around_obstacle():
    g = ObstacleGrid(5, 3)
    g.set_obstacle(2, 0, True)
    g.set_obstacle(2, 1, True)
    f = Pathfinder(g)
    path = f.find((0, 1), (4, 1))
    assert path[-1] == (4, 1)
    assert (2, 0) not in path
    assert (2, 1) not in path

def test_diagonal_path():
    g = ObstacleGrid(5, 5)
    f = Pathfinder(g, diagonal=True)
    path = f.find((0, 0), (4, 4))
    assert path[-1] == (4, 4)
    assert len(path) == 5   # diagonal: 5 steps

def test_diagonal_no_corner_cutting():
    g = ObstacleGrid(5, 5)
    g.set_obstacle(1, 0, True)
    g.set_obstacle(0, 1, True)
    f = Pathfinder(g, diagonal=True)
    path = f.find((0, 0), (2, 2))
    assert (1, 1) not in path   # can't cut through corner

def test_path_includes_start_and_goal():
    g = ObstacleGrid(10, 10)
    path = Pathfinder(g).find((1, 1), (8, 8))
    assert path[0]  == (1, 1)
    assert path[-1] == (8, 8)

def test_pathfinder_repr():
    g = ObstacleGrid(5, 5)
    assert "Pathfinder" in repr(Pathfinder(g))

def test_grid_repr():
    assert "ObstacleGrid" in repr(ObstacleGrid(5, 5))
