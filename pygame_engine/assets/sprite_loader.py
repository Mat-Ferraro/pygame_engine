"""
assets/sprite_loader.py

Image and spritesheet loading for pygame_engine.

All image file access goes through ``SpriteLoader``. It handles path
resolution, caching, format conversion, and placeholder generation for
missing files in debug mode.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from pygame_engine.assets.paths import PathResolver


_PLACEHOLDER_COLOUR = (200, 60, 200)    # magenta — obviously wrong
_PLACEHOLDER_SIZE   = (64, 64)


class SpriteLoader:
    """Loads and caches image surfaces."""

    def __init__(self, paths: PathResolver) -> None:
        self._paths = paths
        self._cache: dict[str, pygame.Surface] = {}

    def load(
        self,
        relative: str,
        convert_alpha: bool = True,
        debug: bool = False,
    ) -> pygame.Surface:
        """
        Load a single image, returning a cached copy on repeat calls.

        The cache key is the resolved absolute path string.

        Args:
            relative:      Path relative to ``asset_root`` or
                           ``asset_root/images/``. Both are tried.
            convert_alpha: Call ``convert_alpha()`` for fast alpha blitting.
            debug:         If True, return a placeholder on missing files.

        Returns:
            A ``pygame.Surface``.

        Raises:
            FileNotFoundError: If the file is missing and debug is False.
        """
        path = self._resolve_image_path(relative)
        key  = str(path)

        if key in self._cache:
            return self._cache[key]

        if not path.exists():
            if debug:
                surf = self._make_placeholder(*_PLACEHOLDER_SIZE)
                self._cache[key] = surf
                return surf
            raise FileNotFoundError(
                f"Image not found: {path}\n"
                f"  (looked for '{relative}' under {self._paths.root})"
            )

        surf = pygame.image.load(str(path))
        if convert_alpha:
            surf = surf.convert_alpha()
        else:
            surf = surf.convert()

        self._cache[key] = surf
        return surf

    def load_sheet(
        self,
        relative: str,
        frame_width: int,
        frame_height: int,
        convert_alpha: bool = True,
        debug: bool = False,
    ) -> list[pygame.Surface]:
        """
        Load a spritesheet and slice it into frames.

        Frames are extracted left-to-right, top-to-bottom.

        Args:
            relative:     Path relative to asset root.
            frame_width:  Width of each frame in pixels.
            frame_height: Height of each frame in pixels.
            convert_alpha: Convert frames for alpha blitting.
            debug:        Return placeholder frames on missing files.

        Returns:
            List of ``pygame.Surface`` frames.
        """
        sheet = self.load(relative, convert_alpha=convert_alpha, debug=debug)
        w, h  = sheet.get_size()

        frames: list[pygame.Surface] = []
        for row in range(h // frame_height):
            for col in range(w // frame_width):
                rect  = pygame.Rect(col * frame_width, row * frame_height,
                                    frame_width, frame_height)
                frame = sheet.subsurface(rect).copy()
                frames.append(frame)

        return frames

    def clear(self) -> None:
        """Clear the image cache."""
        self._cache.clear()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _resolve_image_path(self, relative: str) -> Path:
        """Try images/ subdirectory first, then asset root directly."""
        candidate = self._paths.image(relative)
        if candidate.exists():
            return candidate
        return self._paths.resolve(relative)

    @staticmethod
    def _make_placeholder(width: int, height: int) -> pygame.Surface:
        """Return a magenta rect with a cross — obviously a missing asset."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((*_PLACEHOLDER_COLOUR, 200))
        pygame.draw.line(surf, (255, 255, 255), (0, 0), (width, height), 2)
        pygame.draw.line(surf, (255, 255, 255), (width, 0), (0, height), 2)
        return surf
