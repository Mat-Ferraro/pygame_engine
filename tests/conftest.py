"""
Provides headless pygame initialisation so tests can use pygame
primitives (Rect, Surface, etc.) without opening a display window.
This makes the test suite runnable in CI environments with no display.

Also ensures the repository root is on ``sys.path`` so tests can import
top-level packages that are NOT pip-installed — notably the ``editor``
package, which lives at the repo root alongside ``pygame_engine`` but
is run via ``python -m editor`` rather than being installed. Without
this, ``from editor.scene_loader import ...`` fails during collection
with ``ModuleNotFoundError: No module named 'editor'`` even though the
same import works when running the editor directly.
"""

import sys
from pathlib import Path

import pytest
import pygame


# ── Import path ────────────────────────────────────────────────────────────────
# This file lives at <repo>/tests/conftest.py, so the repo root is two
# levels up from this file's parent. Putting it at the front of sys.path
# makes top-level packages (editor, examples, game_template) importable
# in tests regardless of the current working directory or whether the
# project has been pip-installed.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


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
