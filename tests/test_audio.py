"""
Tests for pygame_engine.audio.audio_manager.AudioManager.

All tests mock pygame.mixer so no real audio hardware is required.
The mixer is patched at the module level for each test.

Note: The new AudioManager uses a bus topology. The flat properties
(master_volume, music_volume, sfx_volume, muted) are shims that delegate
to buses. Tests that previously set private attributes directly (_master_volume
etc.) now use the flat property setters instead.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pygame_engine.audio.audio_manager import AudioManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_manager() -> AudioManager:
    """Return a fresh AudioManager (no pygame init needed)."""
    return AudioManager()


def mock_mixer_init(init: bool = True):
    """Context manager that patches pygame.mixer.get_init."""
    return patch("pygame.mixer.get_init", return_value=init)


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_master_volume() -> None:
    am = make_manager()
    assert am.master_volume == 1.0


def test_default_music_volume() -> None:
    am = make_manager()
    assert am.music_volume == 1.0


def test_default_sfx_volume() -> None:
    am = make_manager()
    assert am.sfx_volume == 1.0


def test_default_not_muted() -> None:
    am = make_manager()
    assert am.muted is False


def test_default_music_not_playing() -> None:
    with patch("pygame.mixer.music") as mock_music:
        mock_music.get_busy.return_value = False
        am = make_manager()
        assert am.music_playing is False


def test_default_music_not_paused() -> None:
    am = make_manager()
    assert am.music_paused is False


# ── Volume setters ────────────────────────────────────────────────────────────

def test_master_volume_setter_clamps_above_one() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.master_volume = 2.0
    assert am.master_volume == 1.0


def test_master_volume_setter_clamps_below_zero() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.master_volume = -0.5
    assert am.master_volume == 0.0


def test_master_volume_midpoint() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.master_volume = 0.5
    assert abs(am.master_volume - 0.5) < 1e-9


def test_music_volume_setter_clamps() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.music_volume = 1.5
    assert am.music_volume == 1.0


def test_sfx_volume_setter_clamps() -> None:
    am = make_manager()
    am.sfx_volume = -1.0
    assert am.sfx_volume == 0.0


def test_sfx_volume_setter_midpoint() -> None:
    am = make_manager()
    am.sfx_volume = 0.75
    assert abs(am.sfx_volume - 0.75) < 1e-9


# ── Effective volume calculation ──────────────────────────────────────────────

def test_effective_music_volume_is_master_times_music() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.master_volume = 0.8
        am.music_volume  = 0.5
    assert abs(am._effective_music_volume - 0.4) < 1e-9


def test_effective_sfx_volume_is_master_times_sfx() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.master_volume = 0.5
    am.sfx_volume = 0.6
    assert abs(am._effective_sfx_volume - 0.3) < 1e-9


def test_effective_music_volume_zero_when_muted() -> None:
    am = make_manager()
    am.master.muted.value = True
    assert am._effective_music_volume == 0.0


def test_effective_sfx_volume_zero_when_muted() -> None:
    am = make_manager()
    am.master.muted.value = True
    assert am._effective_sfx_volume == 0.0


# ── Mute ──────────────────────────────────────────────────────────────────────

def test_mute_silences_without_losing_volume() -> None:
    am = make_manager()
    am.music_volume = 0.7
    with mock_mixer_init(False):
        am.muted = True
    assert am.muted is True
    assert am.music_volume == 0.7   # preserved


def test_unmute_restores_volume() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.muted = True
        am.muted = False
    assert am.muted is False


def test_toggle_mute_switches_state() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        result = am.toggle_mute()
    assert result is True
    assert am.muted is True


def test_toggle_mute_returns_new_state() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.toggle_mute()
        result = am.toggle_mute()
    assert result is False
    assert am.muted is False


# ── Music ─────────────────────────────────────────────────────────────────────

def test_play_music_noop_when_mixer_uninitialised() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.play_music("music.ogg")   # should not raise
    assert am._music_path is None


def test_play_music_loads_and_plays() -> None:
    am = make_manager()
    with mock_mixer_init(True),          patch("pygame.mixer.music") as mock_music:
        mock_music.get_busy.return_value = True
        am.play_music("theme.ogg", loops=-1)
        mock_music.load.assert_called_once_with("theme.ogg")
        mock_music.play.assert_called_once()


def test_play_music_stores_path() -> None:
    am = make_manager()
    with mock_mixer_init(True), patch("pygame.mixer.music"):
        am.play_music("theme.ogg")
    assert am._music_path == "theme.ogg"


def test_stop_music_calls_stop() -> None:
    am = make_manager()
    with patch("pygame.mixer.music") as mock_music:
        am.stop_music()
        mock_music.stop.assert_called_once()


def test_stop_music_with_fade_calls_fadeout() -> None:
    am = make_manager()
    with patch("pygame.mixer.music") as mock_music:
        am.stop_music(fade_out_ms=500)
        mock_music.fadeout.assert_called_once_with(500)


def test_pause_music_when_busy() -> None:
    am = make_manager()
    with patch("pygame.mixer.music") as mock_music:
        mock_music.get_busy.return_value = True
        am.pause_music()
        mock_music.pause.assert_called_once()
        assert am.music_paused is True


def test_pause_music_noop_when_not_busy() -> None:
    am = make_manager()
    with patch("pygame.mixer.music") as mock_music:
        mock_music.get_busy.return_value = False
        am.pause_music()
        mock_music.pause.assert_not_called()


def test_resume_music_when_paused() -> None:
    am = make_manager()
    am._music_paused = True
    with patch("pygame.mixer.music") as mock_music:
        am.resume_music()
        mock_music.unpause.assert_called_once()
        assert am.music_paused is False


def test_resume_music_noop_when_not_paused() -> None:
    am = make_manager()
    am._music_paused = False
    with patch("pygame.mixer.music") as mock_music:
        am.resume_music()
        mock_music.unpause.assert_not_called()


def test_music_playing_false_when_paused() -> None:
    am = make_manager()
    am._music_paused = True
    with patch("pygame.mixer.music") as mock_music:
        mock_music.get_busy.return_value = True
        assert am.music_playing is False


def test_music_playing_true_when_busy_and_not_paused() -> None:
    am = make_manager()
    am._music_paused = False
    with patch("pygame.mixer.music") as mock_music:
        mock_music.get_busy.return_value = True
        assert am.music_playing is True


# ── Sound effects ─────────────────────────────────────────────────────────────

def test_play_sfx_returns_none_for_none_sound() -> None:
    am = make_manager()
    result = am.play_sfx(None)
    assert result is None


def test_play_sfx_returns_none_when_mixer_uninitialised() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        sound = MagicMock()
        result = am.play_sfx(sound)
    assert result is None


def test_play_sfx_sets_volume_and_plays() -> None:
    am = make_manager()
    sound = MagicMock()
    channel = MagicMock()
    sound.play.return_value = channel

    with mock_mixer_init(True):
        result = am.play_sfx(sound, volume=1.0)

    sound.set_volume.assert_called_once()
    sound.play.assert_called_once_with(loops=0)
    assert result is channel


def test_play_sfx_volume_scaled_by_master_and_sfx() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.master_volume = 0.5
    am.sfx_volume = 0.8
    sound = MagicMock()
    sound.play.return_value = MagicMock()

    with mock_mixer_init(True):
        am.play_sfx(sound, volume=1.0)

    # effective = master(0.5) * sfx(0.8) * per_call(1.0) = 0.4
    call_args = sound.set_volume.call_args[0][0]
    assert abs(call_args - 0.4) < 1e-6


def test_play_sfx_volume_zero_when_muted() -> None:
    am = make_manager()
    am.master.muted.value = True
    sound = MagicMock()
    sound.play.return_value = MagicMock()

    with mock_mixer_init(True):
        am.play_sfx(sound)

    call_args = sound.set_volume.call_args[0][0]
    assert call_args == 0.0


# ── Shutdown ──────────────────────────────────────────────────────────────────

def test_shutdown_stops_all_audio() -> None:
    am = make_manager()
    with mock_mixer_init(True),          patch("pygame.mixer.music") as mock_music,          patch("pygame.mixer.stop") as mock_stop:
        am.shutdown()
        mock_music.stop.assert_called_once()
        mock_stop.assert_called_once()


def test_shutdown_noop_when_mixer_uninitialised() -> None:
    am = make_manager()
    with mock_mixer_init(False):
        am.shutdown()   # should not raise
