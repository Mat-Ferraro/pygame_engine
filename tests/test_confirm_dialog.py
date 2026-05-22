from pygame_engine.app.render_context import RenderContext
from pygame_engine.theme.runtime import get_theme

def _ctx():
    return RenderContext(theme=get_theme())

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from pygame_engine.ui.feedback.confirm_dialog import ConfirmDialog


class _FakeSceneManager:
    def __init__(self):
        self.pops = 0
        self.pushes = []

    def pop(self):
        self.pops += 1

    def push(self, scene):
        self.pushes.append(scene)


class _FakeApp:
    def __init__(self):
        self.scene_manager = _FakeSceneManager()
        self.screen = pygame.display.get_surface()


def make_dialog(**kwargs):
    app = _FakeApp()
    defaults = dict(app=app, message="Are you sure?")
    defaults.update(kwargs)
    dlg = ConfirmDialog(**defaults)
    dlg._app = app
    return dlg, app


def ev(type_, **kwargs):
    return pygame.event.Event(type_, **kwargs)


# ── Construction ──────────────────────────────────────────────────────────────

def test_message_stored():
    dlg, _ = make_dialog(message="Delete this hero?")
    assert dlg._message == "Delete this hero?"


def test_confirm_label_default():
    dlg, _ = make_dialog()
    assert dlg._confirm_label == "Confirm"


def test_cancel_label_default():
    dlg, _ = make_dialog()
    assert dlg._cancel_label == "Cancel"


def test_custom_labels():
    dlg, _ = make_dialog(confirm_label="Yes, delete", cancel_label="Go back")
    assert dlg._confirm_label == "Yes, delete"
    assert dlg._cancel_label == "Go back"


def test_danger_flag_default_true():
    dlg, _ = make_dialog()
    assert dlg._danger is True


def test_danger_flag_false():
    dlg, _ = make_dialog(danger=False)
    assert dlg._danger is False


# ── Escape cancels ────────────────────────────────────────────────────────────

def test_escape_calls_on_cancel():
    called = []
    dlg, app = make_dialog(on_cancel=lambda: called.append(True))
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
    assert called == [True]


def test_escape_pops_scene():
    dlg, app = make_dialog()
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
    assert app.scene_manager.pops == 1


def test_escape_without_callback_does_not_raise():
    dlg, app = make_dialog(on_cancel=None)
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
    assert app.scene_manager.pops == 1


# ── Enter confirms ────────────────────────────────────────────────────────────

def test_enter_calls_on_confirm():
    called = []
    dlg, _ = make_dialog(on_confirm=lambda: called.append(True))
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
    assert called == [True]


def test_enter_pops_scene():
    dlg, app = make_dialog()
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
    assert app.scene_manager.pops == 1


def test_enter_without_callback_does_not_raise():
    dlg, app = make_dialog(on_confirm=None)
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
    assert app.scene_manager.pops == 1


# ── Callbacks not both called ─────────────────────────────────────────────────

def test_confirm_does_not_call_cancel():
    cancelled = []
    confirmed = []
    dlg, _ = make_dialog(
        on_confirm=lambda: confirmed.append(True),
        on_cancel=lambda: cancelled.append(True),
    )
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
    assert confirmed == [True]
    assert cancelled == []


def test_cancel_does_not_call_confirm():
    cancelled = []
    confirmed = []
    dlg, _ = make_dialog(
        on_confirm=lambda: confirmed.append(True),
        on_cancel=lambda: cancelled.append(True),
    )
    dlg._handle_event(ev(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode=""))
    assert cancelled == [True]
    assert confirmed == []


# ── Dialog rect geometry ──────────────────────────────────────────────────────

def test_dialog_centred_on_screen():
    dlg, _ = make_dialog()
    sw, sh  = pygame.display.get_surface().get_size()
    dlg_r   = dlg._dialog_rect(sw, sh)
    assert dlg_r.centerx == sw // 2
    assert dlg_r.centery == sh // 2


def test_button_rects_inside_dialog():
    dlg, _ = make_dialog()
    sw, sh  = pygame.display.get_surface().get_size()
    dlg_r   = dlg._dialog_rect(sw, sh)
    conf_r, canc_r = dlg._button_rects()
    assert dlg_r.contains(conf_r)
    assert dlg_r.contains(canc_r)


def test_button_rects_do_not_overlap():
    dlg, _ = make_dialog()
    conf_r, canc_r = dlg._button_rects()
    assert not conf_r.colliderect(canc_r)


# ── Push factory ─────────────────────────────────────────────────────────────

def test_push_adds_to_scene_manager():
    app = _FakeApp()
    dlg = ConfirmDialog.push(app=app, message="Sure?")
    assert len(app.scene_manager.pushes) == 1
    assert app.scene_manager.pushes[0]._dlg is dlg


def test_push_returns_dialog_instance():
    app = _FakeApp()
    dlg = ConfirmDialog.push(app=app, message="Proceed?")
    assert isinstance(dlg, ConfirmDialog)


# ── Render ────────────────────────────────────────────────────────────────────

def test_render_does_not_raise():
    surf = pygame.Surface((1920, 1080))
    dlg, _ = make_dialog(message="Confirm deletion?")
    dlg._render(surf, _ctx())


def test_render_multiline_message_does_not_raise():
    surf = pygame.Surface((1920, 1080))
    dlg, _ = make_dialog(message="Line one\nLine two\nLine three")
    dlg._render(surf, _ctx())