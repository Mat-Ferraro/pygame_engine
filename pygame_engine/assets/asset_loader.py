"""
assets/asset_loader.py

Central asset loading and caching for pygame_engine.

``AssetLoader`` is the single entry point for all asset access. It owns
the cache and delegates type-specific loading to the focused helpers in
``fonts.py``, ``sprite_loader.py``, and ``sounds.py``.

Owned by ``Application`` and accessible via ``app.assets``.

Caching policy
--------------
Assets are loaded on first request and cached for the lifetime of the
session. There is no cache invalidation in v1 — if you need a reload,
restart the application.

Cache keys are normalised absolute path strings (for images and sounds)
or ``(path, size, bold, italic)`` tuples (for fonts).

Missing asset behaviour
-----------------------
- Images:  raises ``AssetNotFoundError`` by default. In debug mode,
           returns a placeholder surface (coloured rect with a cross).
- Fonts:   always raises ``AssetNotFoundError`` — font path errors must
           be caught early.
- Sounds:  logs a warning and returns ``None`` — missing sounds are
           non-fatal since audio is optional.

Usage::

    # Via Application (preferred)
    image = app.assets.image("ui/button.png")
    font  = app.assets.font("fonts/inter.ttf", size=18)
    sound = app.assets.sound("sounds/click.wav")

    # Direct construction (e.g. in tools/tests)
    from pygame_engine.assets import AssetLoader
    from pathlib import Path
    loader = AssetLoader(Path("assets"), debug=True)
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pygame

from pygame_engine.assets.fonts import FontCache
from pygame_engine.assets.paths import PathResolver
from pygame_engine.assets.sounds import SoundCache
from pygame_engine.assets.sprite_loader import SpriteLoader


class AssetNotFoundError(FileNotFoundError):
    """Raised when a required asset file cannot be found on disk."""


class AssetLoader:
    """
    Central asset loader and cache for a pygame_engine project.

    Owned by ``Application``, initialised from ``AppConfig.asset_root``.
    All asset access should go through this object.
    """

    def __init__(self, asset_root: Path, debug: bool = False) -> None:
        """
        Args:
            asset_root: Root directory for project assets. Resolved to an
                        absolute path at construction.
            debug:      If True, missing images return placeholder surfaces
                        instead of raising. Useful during development.
        """
        self._debug     = debug
        self._paths     = PathResolver(asset_root)
        self._fonts     = FontCache(self._paths)
        self._sounds    = SoundCache(self._paths)
        self._sprites   = SpriteLoader(self._paths)

    # ── Image loading ─────────────────────────────────────────────────────────

    def image(
        self,
        relative: str,
        convert_alpha: bool = True,
    ) -> pygame.Surface:
        """
        Load and cache an image surface.

        Args:
            relative:      Path relative to ``asset_root/images/``.
                           May also be a full path relative to asset_root.
            convert_alpha: If True, calls ``convert_alpha()`` on load for
                           faster per-pixel blitting. Set False for images
                           without transparency.

        Returns:
            A ``pygame.Surface``.

        Raises:
            AssetNotFoundError: If the file is missing and debug is False.
        """
        return self._sprites.load(relative, convert_alpha=convert_alpha,
                                  debug=self._debug)

    def spritesheet(
        self,
        relative: str,
        frame_width: int,
        frame_height: int,
        convert_alpha: bool = True,
    ) -> list[pygame.Surface]:
        """
        Load a spritesheet and slice it into frames.

        Frames are extracted left-to-right, top-to-bottom.

        Args:
            relative:     Path relative to ``asset_root/images/``.
            frame_width:  Width of each frame in pixels.
            frame_height: Height of each frame in pixels.
            convert_alpha: Convert frames for alpha blitting.

        Returns:
            List of ``pygame.Surface`` frames.

        Raises:
            AssetNotFoundError: If the file is missing and debug is False.
        """
        return self._sprites.load_sheet(relative, frame_width, frame_height,
                                        convert_alpha=convert_alpha,
                                        debug=self._debug)

    # ── Font loading ──────────────────────────────────────────────────────────

    def font(
        self,
        relative: str,
        size: int,
        bold: bool = False,
        italic: bool = False,
    ) -> pygame.font.Font:
        """
        Load and cache a font from a file.

        Args:
            relative: Path relative to ``asset_root/fonts/``.
            size:     Font size in points.
            bold:     Request bold variant.
            italic:   Request italic variant.

        Returns:
            A ``pygame.font.Font``.

        Raises:
            AssetNotFoundError: If the font file cannot be found.
        """
        return self._fonts.load(relative, size, bold=bold, italic=italic)

    def sysfont(
        self,
        name: str,
        size: int,
        bold: bool = False,
        italic: bool = False,
    ) -> pygame.font.Font:
        """
        Load and cache a system font by name.

        This is a convenience wrapper for ``pygame.font.SysFont`` with
        caching. Use for UI text that doesn't need a custom font file.

        Args:
            name:   Comma-separated font name hints (e.g. ``"arial,helvetica"``).
            size:   Font size in points.
            bold:   Request bold.
            italic: Request italic.

        Returns:
            A ``pygame.font.Font``.
        """
        return self._fonts.load_sys(name, size, bold=bold, italic=italic)

    # ── Sound loading ─────────────────────────────────────────────────────────

    def sound(self, relative: str) -> pygame.mixer.Sound | None:
        """
        Load and cache a sound effect.

        Args:
            relative: Path relative to ``asset_root/sounds/``.

        Returns:
            A ``pygame.mixer.Sound``, or ``None`` if the file is missing
            (missing sounds are non-fatal — a warning is logged instead).
        """
        return self._sounds.load(relative)

    # ── Cache management ──────────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """
        Clear all cached assets.

        Assets will be reloaded from disk on next request. Use sparingly —
        typically only needed between major scene transitions or in tooling.
        """
        self._fonts.clear()
        self._sounds.clear()
        self._sprites.clear()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def asset_root(self) -> Path:
        """The resolved asset root directory."""
        return self._paths.root

    @property
    def debug(self) -> bool:
        """True if debug/placeholder mode is active."""
        return self._debug
