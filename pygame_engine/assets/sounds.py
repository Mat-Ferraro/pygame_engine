"""
assets/sounds.py

Sound effect loading and caching for pygame_engine.

``SoundCache`` loads sound effects via ``pygame.mixer.Sound``. Missing
sound files log a warning and return ``None`` — audio is non-fatal.
The caller (typically ``AudioManager``) handles the None case.

This module is for loading sound data only. Playback policy (volume,
channels, music vs effects) belongs in ``audio/audio_manager.py``.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pygame

from pygame_engine.assets.paths import PathResolver


class SoundCache:
    """Loads and caches sound effects."""

    def __init__(self, paths: PathResolver) -> None:
        self._paths = paths
        self._cache: dict[str, pygame.mixer.Sound | None] = {}

    def load(self, relative: str) -> pygame.mixer.Sound | None:
        """
        Load a sound effect, returning a cached instance on repeat calls.

        Missing files log a warning and return None rather than raising.
        The mixer must be initialised before calling this method — it is
        initialised by ``Application._startup`` via ``pygame.init()``.

        Args:
            relative: Path relative to ``asset_root/sounds/``.

        Returns:
            A ``pygame.mixer.Sound``, or ``None`` if not found or if the
            mixer is not available.
        """
        path = self._resolve_sound_path(relative)
        key  = str(path)

        if key in self._cache:
            return self._cache[key]

        if not path.exists():
            warnings.warn(
                f"Sound not found: {path} — audio will be silent for '{relative}'",
                stacklevel=3,
            )
            self._cache[key] = None
            return None

        if not pygame.mixer.get_init():
            warnings.warn(
                "pygame.mixer is not initialised — sound will not play.",
                stacklevel=3,
            )
            self._cache[key] = None
            return None

        try:
            sound = pygame.mixer.Sound(str(path))
            self._cache[key] = sound
            return sound
        except pygame.error as exc:
            warnings.warn(
                f"Failed to load sound '{relative}': {exc}",
                stacklevel=3,
            )
            self._cache[key] = None
            return None

    def clear(self) -> None:
        """Clear the sound cache."""
        self._cache.clear()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _resolve_sound_path(self, relative: str) -> Path:
        """Try sounds/ subdirectory first, then asset root directly."""
        candidate = self._paths.sound(relative)
        if candidate.exists():
            return candidate
        return self._paths.resolve(relative)
