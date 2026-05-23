"""
Tests for DescribedScene — the descriptor-authored scene base class.

Covers: the on_enter build chain (_build_layout → load → root_widget →
_bind_behavior); widget() / find_widget() lookup; _build_layout is
required; on_exit teardown; the resize rebuild; and that _build_layout
is re-runnable.
"""

from __future__ import annotations

import pygame
import pytest

from pygame_engine.scene.described_scene import DescribedScene


# ── Test scenes ───────────────────────────────────────────────────────────────

class _MenuScene(DescribedScene):
    """A minimal described scene: a panel with one button."""

    def __init__(self) -> None:
        super().__init__()
        self.build_count = 0          # how many times _build_layout ran
        self.bound       = False      # did _bind_behavior run

    def _build_layout(self) -> None:
        self.build_count += 1
        screen = self.screen_rect
        with self.layout.builder() as L:
            L.panel("root", x=0, y=0, w=screen.w, h=screen.h)
            L.button("ok_btn", x=10, y=10, w=80, h=30,
                     parent="root", label="OK")

    def _bind_behavior(self) -> None:
        self.bound = True


class _NoLayoutScene(DescribedScene):
    """A described scene that forgets to override _build_layout."""


# ══════════════════════════════════════════════════════════════════════════════
# on_enter build chain
# ══════════════════════════════════════════════════════════════════════════════

def test_on_enter_builds_root_widget() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    assert scene.root_widget is not None


def test_on_enter_runs_build_layout_once() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    assert scene.build_count == 1


def test_on_enter_runs_bind_behavior() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    assert scene.bound is True


def test_missing_build_layout_raises() -> None:
    scene = _NoLayoutScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    with pytest.raises(NotImplementedError):
        scene.on_enter()


# ══════════════════════════════════════════════════════════════════════════════
# widget() / find_widget()
# ══════════════════════════════════════════════════════════════════════════════

def test_widget_lookup_after_enter() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    btn = scene.widget("ok_btn")
    assert btn is not None
    assert btn.label == "OK"


def test_widget_unknown_id_raises() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    with pytest.raises(KeyError):
        scene.widget("not_a_widget")


def test_widget_before_enter_raises() -> None:
    scene = _MenuScene()
    # No on_enter() yet — the tree does not exist.
    with pytest.raises(RuntimeError):
        scene.widget("ok_btn")


def test_find_widget_before_enter_returns_none() -> None:
    scene = _MenuScene()
    assert scene.find_widget("ok_btn") is None


def test_find_widget_unknown_returns_none() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    assert scene.find_widget("not_a_widget") is None


# ══════════════════════════════════════════════════════════════════════════════
# screen_rect
# ══════════════════════════════════════════════════════════════════════════════

def test_screen_rect_is_used_by_build_layout() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 1024, 768))
    scene.on_enter()
    # The root panel was sized to screen_rect.
    root = scene.widget("root")
    assert (root.rect.w, root.rect.h) == (1024, 768)


def test_screen_rect_returns_a_copy() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    r = scene.screen_rect
    r.w = 1            # mutating the returned rect must not affect the scene
    assert scene.screen_rect.w == 800


# ══════════════════════════════════════════════════════════════════════════════
# Resize rebuild
# ══════════════════════════════════════════════════════════════════════════════

def test_on_resize_rebuilds_layout() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    assert scene.build_count == 1

    scene.on_resize(1280, 720)
    # _build_layout ran a second time for the new size.
    assert scene.build_count == 2


def test_on_resize_reflows_geometry() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()

    scene.on_resize(1280, 720)
    root = scene.widget("root")
    assert (root.rect.w, root.rect.h) == (1280, 720)


def test_build_layout_is_rerunnable_no_duplicate_nodes() -> None:
    # Re-running _build_layout must not raise a duplicate-id error.
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    scene.on_resize(1000, 800)        # would raise if descriptor not cleared
    assert scene.layout.node_count == 2


# ══════════════════════════════════════════════════════════════════════════════
# on_exit
# ══════════════════════════════════════════════════════════════════════════════

def test_on_exit_clears_root_widget() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    scene.on_exit()
    assert scene.root_widget is None


def test_on_exit_clears_descriptor() -> None:
    scene = _MenuScene()
    scene.set_screen_rect(pygame.Rect(0, 0, 800, 600))
    scene.on_enter()
    scene.on_exit()
    assert scene.layout.node_count == 0
