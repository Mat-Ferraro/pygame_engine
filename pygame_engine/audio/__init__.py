"""
pygame_engine.audio

Runtime audio management.

Public API::

    from pygame_engine.audio import AudioManager

    # Via Application (preferred):
    app.audio.play_music("music/theme.ogg")
    app.audio.play_sfx(app.assets.sound("click.wav"))
    app.audio.master_volume = 0.8
    app.audio.muted = True
"""

from pygame_engine.audio.audio_manager import AudioManager

__all__ = ["AudioManager"]
