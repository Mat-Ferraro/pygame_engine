"""
Shared pytest fixtures for pygame_engine tests.

Provides headless pygame initialisation so tests can use pygame
primitives (Rect, Surface, etc.) without opening a display window.
This makes the test suite runnable in CI environments with no display.
"""

import pytest
import pygame


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    """Initialise pygame once for the entire test session, then quit."""
    pygame.display.init()
    pygame.font.init()
    yield
    pygame.quit()


@pytest.fixture()
def display_surface():
    """Return a small off-screen surface that acts as a fake display."""
    return pygame.Surface((800, 600))
