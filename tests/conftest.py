"""
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

@pytest.fixture()
def make_ctx():
    """
    Return a factory that builds a default RenderContext for widget tests.

    Usage::

        def test_render(make_ctx, display_surface):
            ctx = make_ctx()
            widget.render(display_surface, ctx)
    """
    from pygame_engine.app.render_context import RenderContext
    from pygame_engine.theme.runtime import get_theme

    def _make():
        return RenderContext(theme=get_theme())

    return _make
