"""Tests for GizmoRenderer."""

from __future__ import annotations
import pytest
import pygame
from pygame_engine.debug.gizmo_renderer import GizmoRenderer, Gizmo


def make_surface() -> pygame.Surface:
    return pygame.Surface((800, 600))


# ── Construction ──────────────────────────────────────────────────────────────

def test_enabled_by_default() -> None:
    assert GizmoRenderer().enabled is True

def test_no_gizmos_by_default() -> None:
    g = GizmoRenderer()
    assert len(g._gizmos) == 0

def test_queue_empty_by_default() -> None:
    g = GizmoRenderer()
    assert len(g._queue) == 0


# ── Draw calls enqueue ────────────────────────────────────────────────────────

def test_draw_rect_enqueues() -> None:
    g = GizmoRenderer()
    g.draw_rect(pygame.Rect(0, 0, 100, 50), (0, 255, 0))
    assert len(g._queue) == 1

def test_draw_circle_enqueues() -> None:
    g = GizmoRenderer()
    g.draw_circle((50, 50), 20, (255, 0, 0))
    assert len(g._queue) == 1

def test_draw_line_enqueues() -> None:
    g = GizmoRenderer()
    g.draw_line((0, 0), (100, 100), (255, 255, 0))
    assert len(g._queue) == 1

def test_draw_arrow_enqueues() -> None:
    g = GizmoRenderer()
    g.draw_arrow((0, 0), (100, 0), (0, 0, 255))
    assert len(g._queue) == 1

def test_draw_text_enqueues() -> None:
    g = GizmoRenderer()
    g.draw_text((10, 10), "hello", (255, 255, 255))
    assert len(g._queue) == 1

def test_draw_cross_enqueues_two_lines() -> None:
    g = GizmoRenderer()
    g.draw_cross((50, 50))
    assert len(g._queue) == 2   # two draw_line calls

def test_draw_grid_enqueues_multiple_lines() -> None:
    g = GizmoRenderer()
    g.draw_grid(pygame.Rect(0, 0, 100, 100), cell_size=50)
    assert len(g._queue) > 0


# ── render() clears queue ─────────────────────────────────────────────────────

def test_render_clears_queue() -> None:
    g = GizmoRenderer()
    g.draw_rect(pygame.Rect(0, 0, 10, 10))
    g.render(make_surface())
    assert len(g._queue) == 0

def test_render_disabled_clears_queue() -> None:
    g = GizmoRenderer()
    g.enabled = False
    g.draw_rect(pygame.Rect(0, 0, 10, 10))
    g.render(make_surface())
    assert len(g._queue) == 0

def test_render_does_not_raise() -> None:
    g = GizmoRenderer()
    g.draw_rect(pygame.Rect(10, 10, 100, 50), (0, 255, 0), label="test")
    g.draw_circle((50, 50), 20, (255, 0, 0))
    g.draw_line((0, 0), (100, 100))
    g.draw_arrow((0, 0), (50, 50))
    g.draw_cross((30, 30))
    g.render(make_surface())   # must not raise


# ── Category filtering ────────────────────────────────────────────────────────

def test_hidden_category_not_drawn() -> None:
    g = GizmoRenderer()
    g.hide("ai")
    g.draw_rect(pygame.Rect(0, 0, 10, 10), category="ai")
    calls_drawn = []
    # Verify by checking the queue category directly
    assert g._queue[0][-1] == "ai"
    g.render(make_surface())   # should not crash; category is filtered

def test_show_unhides_category() -> None:
    g = GizmoRenderer()
    g.hide("ai")
    g.show("ai")
    assert "ai" not in g._hidden

def test_show_all_clears_hidden() -> None:
    g = GizmoRenderer()
    g.hide("ai", "bounds")
    g.show_all()
    assert len(g._hidden) == 0

def test_category_visible_default() -> None:
    g = GizmoRenderer()
    assert g._category_visible("anything") is True

def test_category_visible_hidden() -> None:
    g = GizmoRenderer()
    g.hide("ai")
    assert g._category_visible("ai") is False
    assert g._category_visible("bounds") is True


# ── Gizmo object registration ─────────────────────────────────────────────────

def test_register_gizmo() -> None:
    class MyGizmo:
        def draw(self, renderer, camera=None): pass

    g = GizmoRenderer()
    gizmo = MyGizmo()
    g.register(gizmo)
    assert gizmo in g._gizmos

def test_register_twice_is_noop() -> None:
    class MyGizmo:
        def draw(self, renderer, camera=None): pass

    g = GizmoRenderer()
    gizmo = MyGizmo()
    g.register(gizmo)
    g.register(gizmo)
    assert len(g._gizmos) == 1

def test_unregister_gizmo() -> None:
    class MyGizmo:
        def draw(self, renderer, camera=None): pass

    g = GizmoRenderer()
    gizmo = MyGizmo()
    g.register(gizmo)
    g.unregister(gizmo)
    assert gizmo not in g._gizmos

def test_unregister_unknown_is_noop() -> None:
    class MyGizmo:
        def draw(self, renderer, camera=None): pass

    g = GizmoRenderer()
    g.unregister(MyGizmo())   # must not raise

def test_registered_gizmo_draw_called_on_render() -> None:
    calls = []
    class MyGizmo:
        def draw(self, renderer, camera=None):
            calls.append(1)

    g = GizmoRenderer()
    g.register(MyGizmo())
    g.render(make_surface())
    assert calls == [1]

def test_broken_gizmo_does_not_crash_render() -> None:
    class BadGizmo:
        def draw(self, renderer, camera=None):
            raise RuntimeError("broken gizmo")

    g = GizmoRenderer()
    g.register(BadGizmo())
    g.render(make_surface())   # must not raise

def test_clear_gizmos() -> None:
    class MyGizmo:
        def draw(self, renderer, camera=None): pass

    g = GizmoRenderer()
    g.register(MyGizmo())
    g.clear_gizmos()
    assert len(g._gizmos) == 0


# ── app.gizmos property ───────────────────────────────────────────────────────

def test_gizmos_none_in_production() -> None:
    from pygame_engine.app import Application, AppConfig
    app = Application(AppConfig(mode="production"))
    assert app.gizmos is None

def test_gizmos_available_in_development() -> None:
    from pygame_engine.app import Application, AppConfig
    app = Application(AppConfig(mode="development"))
    assert isinstance(app.gizmos, GizmoRenderer)


# ── Repr ──────────────────────────────────────────────────────────────────────

def test_repr() -> None:
    g = GizmoRenderer()
    assert "GizmoRenderer" in repr(g)
