"""
tests/test_scene_editor_loading.py

Tests for the editor's scene-loading path: load_scene_for_editor()
builds a scene via the EditorAppStub, realises its widget tree, and the
resulting scene renders without raising.

Why this exists
---------------
The editor loads scenes through a lightweight stub Application rather
than the full engine runtime. Bugs in a scene's on_enter() / widget
construction (e.g. assigning a wrong-arity lambda to a Panel method)
only surface when the scene is actually loaded and rendered this way —
not in the engine's own scene tests, which use the real Application.

These tests exercise the full editor load: instantiate via stub, call
on_enter(), confirm the descriptor populated, then render the realised
widget tree to a surface. That covers both the loader plumbing and the
"does this scene actually draw" seam.

Covers: load_scene_for_editor return contract; descriptor node count;
realised root_widget renders without error; layout_path resolution.
"""

from __future__ import annotations

import pygame

from editor.scene_loader import load_scene_for_editor
from examples.example_buttons_described import ButtonDescribedScene

from pygame_engine.app.render_context import RenderContext
from pygame_engine.scene.described_scene import DescribedScene
from pygame_engine.theme.runtime import get_theme


# Editor viewport size the loader builds scenes against, mirroring the
# constants the real editor uses. Values don't need to match exactly —
# any sane viewport works — but a realistic size catches layout maths
# that only breaks at certain dimensions.
_VP_W = 1320
_VP_H = 844


# ── Loader contract ───────────────────────────────────────────────────────────

def test_loader_returns_three_tuple() -> None:
    """load_scene_for_editor returns (scene, status, layout_path)."""
    result = load_scene_for_editor(ButtonDescribedScene, width=_VP_W, height=_VP_H)
    assert isinstance(result, tuple)
    assert len(result) == 3


def test_loader_builds_scene_instance() -> None:
    """The returned scene is a DescribedScene instance, not None."""
    scene, status, _ = load_scene_for_editor(
        ButtonDescribedScene, width=_VP_W, height=_VP_H
    )
    assert scene is not None
    assert isinstance(scene, DescribedScene)
    # Status should be a human-readable success line, not an error.
    assert "Failed" not in status


def test_loader_populates_descriptor() -> None:
    """on_enter() ran and the descriptor has the expected node count.

    ButtonDescribedScene declares 9 nodes (root, title, main_panel,
    three buttons, disabled button, status label, hint label). If the
    descriptor build silently no-ops, this catches it.
    """
    scene, _, _ = load_scene_for_editor(ButtonDescribedScene, width=_VP_W, height=_VP_H)
    assert scene is not None
    descriptor = scene.layout
    assert descriptor is not None
    assert descriptor.node_count == 9


def test_loader_resolves_layout_path() -> None:
    """A layout_path is returned so the editor can wire up Save Layout."""
    _, _, layout_path = load_scene_for_editor(
        ButtonDescribedScene, width=_VP_W, height=_VP_H
    )
    # The example scene lives in a real source file, so a path is derivable.
    assert layout_path is not None
    assert str(layout_path).endswith(".layout.json")


# ── Render seam ─────────────────────────────────────────────────────────────

def test_loaded_scene_renders_without_error() -> None:
    """
    The realised widget tree renders to a surface without raising.

    This is the test that would have caught the Panel `_draw_background`
    lambda-arity bug: the scene loaded fine, the descriptor populated,
    but rendering blew up because the lambda took the wrong number of
    arguments. Logic tests never touched the render path.
    """
    scene, _, _ = load_scene_for_editor(ButtonDescribedScene, width=_VP_W, height=_VP_H)
    assert scene is not None

    surface = pygame.Surface((_VP_W, _VP_H))
    ctx = RenderContext(theme=get_theme())

    # Should not raise.
    scene.render(surface, ctx)


def test_loaded_scene_updates_without_error() -> None:
    """The loaded scene survives an update() tick (edit-mode dt=0)."""
    scene, _, _ = load_scene_for_editor(ButtonDescribedScene, width=_VP_W, height=_VP_H)
    assert scene is not None
    scene.update(0.0)
    scene.update(1.0 / 60.0)


def test_render_is_stable_across_frames() -> None:
    """
    Rendering the same scene several times in a row doesn't raise.

    Guards against state that's only valid on the first render (e.g. a
    cache that's torn down but not rebuilt, or a one-shot resource that
    isn't re-acquired).
    """
    scene, _, _ = load_scene_for_editor(ButtonDescribedScene, width=_VP_W, height=_VP_H)
    assert scene is not None

    surface = pygame.Surface((_VP_W, _VP_H))
    ctx = RenderContext(theme=get_theme())

    for _ in range(5):
        scene.render(surface, ctx)
