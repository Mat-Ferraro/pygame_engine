"""
Tests for pygame_engine.audio.audio_bus.AudioBus and the bus topology
additions to AudioManager.

All existing test_audio.py tests continue to pass unchanged — backward
compatibility of the flat API is tested there. This file covers the new
bus API only.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pygame_engine.audio.audio_bus import AudioBus
from pygame_engine.audio.audio_manager import AudioManager


# ── AudioBus construction ─────────────────────────────────────────────────────

def test_bus_default_volume() -> None:
    bus = AudioBus("test")
    assert bus.volume.value == 1.0


def test_bus_custom_volume() -> None:
    bus = AudioBus("test", volume=0.5)
    assert abs(bus.volume.value - 0.5) < 1e-9


def test_bus_volume_clamped_above_one() -> None:
    bus = AudioBus("test", volume=2.0)
    assert bus.volume.value == 1.0


def test_bus_volume_clamped_below_zero() -> None:
    bus = AudioBus("test", volume=-0.5)
    assert bus.volume.value == 0.0


def test_bus_default_not_muted() -> None:
    bus = AudioBus("test")
    assert bus.muted.value is False


def test_bus_custom_muted() -> None:
    bus = AudioBus("test", muted=True)
    assert bus.muted.value is True


def test_bus_default_respects_time_scale() -> None:
    bus = AudioBus("test")
    assert bus.respects_time_scale is True


def test_bus_name_stored() -> None:
    bus = AudioBus("my_bus")
    assert bus.name == "my_bus"


def test_bus_default_no_parent() -> None:
    bus = AudioBus("test")
    assert bus.parent is None


# ── effective_volume ──────────────────────────────────────────────────────────

def test_effective_volume_no_parent() -> None:
    bus = AudioBus("test", volume=0.6)
    assert abs(bus.effective_volume - 0.6) < 1e-9


def test_effective_volume_zero_when_muted() -> None:
    bus = AudioBus("test", volume=0.8, muted=True)
    assert bus.effective_volume == 0.0


def test_effective_volume_with_parent() -> None:
    parent = AudioBus("parent", volume=0.5)
    child  = AudioBus("child",  volume=0.8)
    child._parent = parent
    assert abs(child.effective_volume - 0.4) < 1e-9


def test_effective_volume_zero_when_parent_muted() -> None:
    parent = AudioBus("parent", muted=True)
    child  = AudioBus("child",  volume=0.8)
    child._parent = parent
    assert child.effective_volume == 0.0


def test_effective_volume_chain_of_three() -> None:
    root   = AudioBus("root",   volume=0.5)
    mid    = AudioBus("mid",    volume=0.8)
    leaf   = AudioBus("leaf",   volume=1.0)
    mid._parent  = root
    leaf._parent = mid
    # 0.5 * 0.8 * 1.0 = 0.4
    assert abs(leaf.effective_volume - 0.4) < 1e-9


def test_effective_volume_paused_by_time() -> None:
    bus = AudioBus("test", volume=0.9, respects_time_scale=True)
    bus._apply_time_scale(0.0)
    assert bus.effective_volume == 0.0


def test_effective_volume_not_paused_when_respects_false() -> None:
    bus = AudioBus("test", volume=0.9, respects_time_scale=False)
    bus._apply_time_scale(0.0)
    assert abs(bus.effective_volume - 0.9) < 1e-9


# ── set_volume ────────────────────────────────────────────────────────────────

def test_set_volume_updates_observable() -> None:
    bus = AudioBus("test")
    bus.set_volume(0.3)
    assert abs(bus.volume.value - 0.3) < 1e-9


def test_set_volume_clamps_above() -> None:
    bus = AudioBus("test")
    bus.set_volume(1.5)
    assert bus.volume.value == 1.0


def test_set_volume_clamps_below() -> None:
    bus = AudioBus("test")
    bus.set_volume(-0.1)
    assert bus.volume.value == 0.0


# ── toggle_mute ───────────────────────────────────────────────────────────────

def test_toggle_mute_returns_true() -> None:
    bus = AudioBus("test")
    result = bus.toggle_mute()
    assert result is True
    assert bus.muted.value is True


def test_toggle_mute_returns_false_on_second_call() -> None:
    bus = AudioBus("test")
    bus.toggle_mute()
    result = bus.toggle_mute()
    assert result is False
    assert bus.muted.value is False


# ── Observable subscriptions ──────────────────────────────────────────────────

def test_volume_observable_notifies_on_change() -> None:
    bus = AudioBus("test")
    received: list = []
    bus.volume.subscribe(lambda old, new: received.append((old, new)))
    bus.set_volume(0.5)
    assert received == [(1.0, 0.5)]


def test_muted_observable_notifies_on_change() -> None:
    bus = AudioBus("test")
    received: list = []
    bus.muted.subscribe(lambda old, new: received.append((old, new)))
    bus.toggle_mute()
    assert received == [(False, True)]


# ── _apply_time_scale ─────────────────────────────────────────────────────────

def test_apply_time_scale_zero_pauses_bus() -> None:
    bus = AudioBus("test", respects_time_scale=True)
    bus._apply_time_scale(0.0)
    assert bus._paused_by_time is True


def test_apply_time_scale_nonzero_unpauses_bus() -> None:
    bus = AudioBus("test", respects_time_scale=True)
    bus._apply_time_scale(0.0)
    bus._apply_time_scale(1.0)
    assert bus._paused_by_time is False


def test_apply_time_scale_ignored_when_respects_false() -> None:
    bus = AudioBus("ui", respects_time_scale=False)
    bus._apply_time_scale(0.0)
    assert bus._paused_by_time is False


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr_contains_name_and_volume() -> None:
    bus = AudioBus("music", volume=0.7)
    r = repr(bus)
    assert "music" in r
    assert "0.70" in r


def test_repr_shows_muted() -> None:
    bus = AudioBus("sfx", muted=True)
    assert "[muted]" in repr(bus)


# ══════════════════════════════════════════════════════════════════════════════
# AudioManager bus topology tests
# ══════════════════════════════════════════════════════════════════════════════

def test_manager_has_four_built_in_buses() -> None:
    am = AudioManager()
    assert hasattr(am, "master")
    assert hasattr(am, "music")
    assert hasattr(am, "sfx")
    assert hasattr(am, "ui")


def test_music_parent_is_master() -> None:
    am = AudioManager()
    assert am.music.parent is am.master


def test_sfx_parent_is_master() -> None:
    am = AudioManager()
    assert am.sfx.parent is am.master


def test_ui_parent_is_master() -> None:
    am = AudioManager()
    assert am.ui.parent is am.master


def test_ui_bus_does_not_respect_time_scale() -> None:
    am = AudioManager()
    assert am.ui.respects_time_scale is False


def test_music_bus_respects_time_scale() -> None:
    am = AudioManager()
    assert am.music.respects_time_scale is True


def test_sfx_bus_respects_time_scale() -> None:
    am = AudioManager()
    assert am.sfx.respects_time_scale is True


def test_master_does_not_respect_time_scale() -> None:
    """Master bus is never paused by time — child buses apply the policy."""
    am = AudioManager()
    assert am.master.respects_time_scale is False


# ── create_bus ────────────────────────────────────────────────────────────────

def test_create_bus_returns_audio_bus() -> None:
    am  = AudioManager()
    bus = am.create_bus("ambient")
    assert isinstance(bus, AudioBus)


def test_create_bus_default_parent_is_master() -> None:
    am  = AudioManager()
    bus = am.create_bus("ambient")
    assert bus.parent is am.master


def test_create_bus_custom_parent() -> None:
    am  = AudioManager()
    bus = am.create_bus("footstep", parent=am.sfx)
    assert bus.parent is am.sfx


def test_create_bus_duplicate_name_raises() -> None:
    am = AudioManager()
    am.create_bus("ambient")
    with pytest.raises(ValueError, match="already exists"):
        am.create_bus("ambient")


def test_get_bus_returns_registered_bus() -> None:
    am = AudioManager()
    assert am.get_bus("music") is am.music
    assert am.get_bus("sfx")   is am.sfx
    assert am.get_bus("ui")    is am.ui


def test_get_bus_unknown_raises() -> None:
    am = AudioManager()
    with pytest.raises(KeyError):
        am.get_bus("nonexistent")


# ── update() / time-scale policy ─────────────────────────────────────────────

def test_update_pauses_music_and_sfx_at_time_scale_zero() -> None:
    am = AudioManager()
    am.update(0.0)
    assert am.music._paused_by_time is True
    assert am.sfx._paused_by_time   is True


def test_update_does_not_pause_ui_at_time_scale_zero() -> None:
    am = AudioManager()
    am.update(0.0)
    assert am.ui._paused_by_time is False


def test_update_unpauses_on_resume() -> None:
    am = AudioManager()
    am.update(0.0)
    am.update(1.0)
    assert am.music._paused_by_time is False
    assert am.sfx._paused_by_time   is False


# ── Backward-compat flat API via bus topology ─────────────────────────────────

def test_flat_master_volume_reads_from_bus() -> None:
    am = AudioManager()
    am.master.set_volume(0.6)
    assert abs(am.master_volume - 0.6) < 1e-9


def test_flat_master_volume_writes_to_bus() -> None:
    am = AudioManager()
    with patch("pygame.mixer.get_init", return_value=False):
        am.master_volume = 0.4
    assert abs(am.master.volume.value - 0.4) < 1e-9


def test_flat_music_volume_writes_to_bus() -> None:
    am = AudioManager()
    with patch("pygame.mixer.get_init", return_value=False):
        am.music_volume = 0.7
    assert abs(am.music.volume.value - 0.7) < 1e-9


def test_flat_sfx_volume_writes_to_bus() -> None:
    am = AudioManager()
    am.sfx_volume = 0.3
    assert abs(am.sfx.volume.value - 0.3) < 1e-9


def test_flat_muted_reads_from_master_bus() -> None:
    am = AudioManager()
    am.master.muted.value = True
    assert am.muted is True


def test_flat_muted_writes_to_master_bus() -> None:
    am = AudioManager()
    with patch("pygame.mixer.get_init", return_value=False):
        am.muted = True
    assert am.master.muted.value is True


def test_flat_toggle_mute_toggles_master_bus() -> None:
    am = AudioManager()
    with patch("pygame.mixer.get_init", return_value=False):
        result = am.toggle_mute()
    assert result is True
    assert am.master.muted.value is True


# ── Effective volume through flat API ─────────────────────────────────────────

def test_effective_sfx_volume_uses_master_and_sfx_buses() -> None:
    am = AudioManager()
    am.master.set_volume(0.5)
    am.sfx.set_volume(0.8)
    assert abs(am._effective_sfx_volume - 0.4) < 1e-9


def test_effective_music_volume_zero_when_master_muted() -> None:
    am = AudioManager()
    with patch("pygame.mixer.get_init", return_value=False):
        am.muted = True
    assert am._effective_music_volume == 0.0


# ── play_sfx bus routing ──────────────────────────────────────────────────────

def test_play_sfx_routes_to_sfx_bus_by_default() -> None:
    """play_sfx uses sfx bus effective volume by default."""
    am = AudioManager()
    am.sfx.set_volume(0.5)
    sound = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    sound.play.return_value = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    with patch("pygame.mixer.get_init", return_value=True):
        am.play_sfx(sound, volume=1.0, bus="sfx")
    vol_set = sound.set_volume.call_args[0][0]
    # effective = master(1.0) * sfx(0.5) * per_call(1.0) = 0.5
    assert abs(vol_set - 0.5) < 1e-6


def test_play_sfx_routes_to_ui_bus() -> None:
    """play_sfx with bus="ui" uses ui bus effective volume."""
    am = AudioManager()
    am.ui.set_volume(0.9)
    sound = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    sound.play.return_value = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    with patch("pygame.mixer.get_init", return_value=True):
        am.play_sfx(sound, volume=1.0, bus="ui")
    vol_set = sound.set_volume.call_args[0][0]
    assert abs(vol_set - 0.9) < 1e-6


def test_play_sfx_ui_bus_plays_when_sfx_paused_by_time() -> None:
    """UI sounds are audible even when sfx bus is time-paused."""
    am = AudioManager()
    am.update(0.0)   # pause sfx and music
    assert am.sfx._paused_by_time is True
    assert am.ui._paused_by_time  is False
    # UI bus should still have effective volume > 0
    assert am.ui.effective_volume > 0.0
