"""
assets/fonts.py

Font loading and caching for pygame_engine.

``FontCache`` loads fonts from file or by system name, caching each
unique (path, size, bold, italic) combination. Repeat calls for the
same font and size return the cached instance without re-loading.

Font errors always raise immediately — a missing font path is a
configuration problem that must be fixed, not silently ignored.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from pygame_engine.assets.paths import PathResolver


# Cache key: (path_or_name, size, bold, italic)
_FontKey = tuple[str, int, bool, bool]


class FontCache:
    """Loads and caches font objects."""

    def __init__(self, paths: PathResolver) -> None:
        self._paths = paths
        self._cache: dict[_FontKey, pygame.font.Font] = {}

    def load(
        self,
        relative: str,
        size: int,
        bold:   bool = False,
        italic: bool = False,
    ) -> pygame.font.Font:
        """
        Load a font from a file, returning a cached instance on repeat calls.

        Args:
            relative: Path relative to ``asset_root/fonts/``.
            size:     Font size in points.
            bold:     Request bold variant (applied via pygame, not a separate
                      font file).
            italic:   Request italic variant.

        Returns:
            A ``pygame.font.Font``.

        Raises:
            FileNotFoundError: If the font file cannot be found.
        """
        path = self._paths.font(relative)
        key: _FontKey = (str(path), size, bold, italic)

        if key in self._cache:
            return self._cache[key]

        if not path.exists():
            raise FileNotFoundError(
                f"Font not found: {path}\n"
                f"  (looked for '{relative}' under {self._paths.root / 'fonts'})"
            )

        font = pygame.font.Font(str(path), size)
        # pygame.font.Font doesn't take bold/italic in constructor —
        # set them as attributes if the font object supports it
        if bold:
            font.bold = True
        if italic:
            font.italic = True

        self._cache[key] = font
        return font

    def load_sys(
        self,
        name: str,
        size: int,
        bold:   bool = False,
        italic: bool = False,
    ) -> pygame.font.Font:
        """
        Load a system font by name, returning a cached instance.

        Args:
            name:   Comma-separated font name hints.
            size:   Font size in points.
            bold:   Request bold.
            italic: Request italic.

        Returns:
            A ``pygame.font.Font``.
        """
        key: _FontKey = (f"sys:{name}", size, bold, italic)

        if key in self._cache:
            return self._cache[key]

        font = pygame.font.SysFont(name, size, bold=bold, italic=italic)
        self._cache[key] = font
        return font

    def clear(self) -> None:
        """Clear the font cache."""
        self._cache.clear()
