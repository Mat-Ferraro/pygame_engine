"""
SpriteAtlas — pack multiple surfaces into one for efficient blitting.

A SpriteAtlas packs many small named surfaces into a single large surface.
Blitting from one large surface is faster than blitting from many small
ones because it avoids repeated texture state changes.

Typical workflow
----------------
1. Build the atlas once (offline or at startup) using ``AtlasPacker``.
2. Load it at game startup with ``SpriteAtlas.from_surfaces()`` or
   ``SpriteAtlas.load()``.
3. Blit regions using ``atlas.blit(surface, name, dest)``.

Usage::

    from pygame_engine.atlas import AtlasPacker, SpriteAtlas

    # Build at startup from a dict of surfaces
    packer = AtlasPacker(max_size=2048)
    packer.add("player_idle",  idle_surface)
    packer.add("player_run",   run_surface)
    packer.add("coin",         coin_surface)
    atlas = packer.build()

    # Blit in render loop
    atlas.blit(screen, "player_idle", dest=(100, 200))

    # Save to disk (offline tool / build step)
    packer.save(Path("assets/images/ui.atlas.png"),
                Path("assets/images/ui.atlas.json"))

    # Load from disk
    atlas = SpriteAtlas.load(Path("assets/images/ui.atlas.png"),
                             Path("assets/images/ui.atlas.json"))
"""

from __future__ import annotations

import json
from pathlib import Path

import pygame


class SpriteAtlas:
    """
    A packed atlas: one surface + a registry of named sub-rects.

    Construct via ``AtlasPacker.build()``, ``SpriteAtlas.from_surfaces()``,
    or ``SpriteAtlas.load()``. Do not construct directly.

    Args:
        surface:  The packed atlas surface.
        regions:  Dict mapping name → ``pygame.Rect`` within the surface.
    """

    def __init__(
        self,
        surface: pygame.Surface,
        regions: dict[str, pygame.Rect],
    ) -> None:
        self._surface = surface
        self._regions = dict(regions)

    # ── Factory methods ───────────────────────────────────────────────────────

    @classmethod
    def from_surfaces(
        cls,
        surfaces:  dict[str, pygame.Surface],
        max_size:  int = 2048,
        padding:   int = 1,
    ) -> "SpriteAtlas":
        """
        Pack a dict of named surfaces into an atlas.

        Uses a simple shelf-packing algorithm (left-to-right, shelf-by-shelf).
        For best results, sort surfaces by height descending before passing.

        Args:
            surfaces: ``{name: surface}`` dict.
            max_size: Maximum atlas width and height in pixels.
            padding:  Pixels of transparent padding between sprites.

        Returns:
            A new ``SpriteAtlas``.

        Raises:
            ValueError: If any surface exceeds ``max_size``.
        """
        packer = AtlasPacker(max_size=max_size, padding=padding)
        for name, surf in surfaces.items():
            packer.add(name, surf)
        return packer.build()

    @classmethod
    def load(
        cls,
        image_path: Path,
        meta_path:  Path,
    ) -> "SpriteAtlas":
        """
        Load an atlas from a PNG image and a JSON metadata file.

        The JSON file must be in the format produced by ``AtlasPacker.save()``.

        Args:
            image_path: Path to the packed PNG.
            meta_path:  Path to the JSON metadata file.
        """
        raw     = pygame.image.load(str(image_path))
        # convert_alpha() requires an active display — use it only when
        # a display is available, otherwise keep the raw surface.
        try:
            surface = raw.convert_alpha()
        except pygame.error:
            surface = raw
        meta    = json.loads(meta_path.read_text(encoding="utf-8"))
        regions = {
            name: pygame.Rect(r["x"], r["y"], r["w"], r["h"])
            for name, r in meta["regions"].items()
        }
        return cls(surface, regions)

    # ── Public API ────────────────────────────────────────────────────────────

    def blit(
        self,
        dest_surface: pygame.Surface,
        name:         str,
        dest:         tuple[int, int] | pygame.Rect,
    ) -> pygame.Rect:
        """
        Blit a named sprite from the atlas onto ``dest_surface``.

        Args:
            dest_surface: The target surface to draw onto.
            name:         Registered name of the sprite.
            dest:         Top-left (x, y) or Rect on the destination surface.

        Returns:
            The affected rect on ``dest_surface``.

        Raises:
            KeyError: If ``name`` is not registered in this atlas.
        """
        region = self.get_rect(name)
        if isinstance(dest, pygame.Rect):
            dest = (dest.x, dest.y)
        return dest_surface.blit(self._surface, dest, region)

    def get_rect(self, name: str) -> pygame.Rect:
        """
        Return the source rect for ``name`` within the atlas surface.

        Useful when you want to blit manually or pass the region to
        another system.

        Raises:
            KeyError: If ``name`` is not registered.
        """
        if name not in self._regions:
            raise KeyError(
                f"Sprite {name!r} not found in atlas. "
                f"Available: {sorted(self._regions)[:5]}{'...' if len(self._regions) > 5 else ''}"
            )
        return pygame.Rect(self._regions[name])

    def get_surface(self, name: str) -> pygame.Surface:
        """
        Return a new Surface containing just the named sprite.

        This allocates a new surface — prefer ``blit()`` in render loops.
        Use this when you need a standalone surface (e.g. for AnimationPlayer).

        Raises:
            KeyError: If ``name`` is not registered.
        """
        region = self.get_rect(name)
        surf   = pygame.Surface((region.width, region.height), pygame.SRCALPHA)
        surf.blit(self._surface, (0, 0), region)
        return surf

    def has(self, name: str) -> bool:
        """Return True if ``name`` is registered in this atlas."""
        return name in self._regions

    @property
    def surface(self) -> pygame.Surface:
        """The packed atlas surface."""
        return self._surface

    @property
    def names(self) -> list[str]:
        """Sorted list of all registered sprite names."""
        return sorted(self._regions)

    @property
    def count(self) -> int:
        """Number of sprites packed in this atlas."""
        return len(self._regions)

    @property
    def size(self) -> tuple[int, int]:
        """Width and height of the atlas surface in pixels."""
        return self._surface.get_size()

    def __repr__(self) -> str:
        w, h = self.size
        return f"SpriteAtlas({self.count} sprites, {w}×{h}px)"


class AtlasPacker:
    """
    Packs named surfaces into a ``SpriteAtlas`` using shelf packing.

    The packing algorithm places sprites left-to-right on a "shelf" until
    a shelf is full, then starts a new shelf below. It is fast and produces
    reasonable packing density for sprites of similar heights.

    Args:
        max_size: Maximum atlas width and height. Default 2048.
        padding:  Transparent pixels between sprites. Default 1.
    """

    def __init__(self, max_size: int = 2048, padding: int = 1) -> None:
        self._max_size = max_size
        self._padding  = padding
        self._items:   list[tuple[str, pygame.Surface]] = []

    def add(self, name: str, surface: pygame.Surface) -> "AtlasPacker":
        """
        Register a surface for packing.

        Args:
            name:    Unique name for this sprite.
            surface: The surface to pack.

        Returns:
            self — for chaining.

        Raises:
            ValueError: If a surface exceeds ``max_size``.
        """
        w, h = surface.get_size()
        if w > self._max_size or h > self._max_size:
            raise ValueError(
                f"Surface {name!r} ({w}×{h}) exceeds atlas max_size {self._max_size}."
            )
        self._items.append((name, surface))
        return self

    def build(self) -> SpriteAtlas:
        """
        Pack all registered surfaces and return a ``SpriteAtlas``.

        Surfaces are sorted by height descending before packing for better
        density. The atlas size grows as needed up to ``max_size``.

        Returns:
            A new ``SpriteAtlas``.

        Raises:
            ValueError: If the packed sprites do not fit within ``max_size``.
        """
        if not self._items:
            # Empty atlas — 1×1 transparent surface
            surf = pygame.Surface((1, 1), pygame.SRCALPHA)
            return SpriteAtlas(surf, {})

        pad     = self._padding
        # Sort tallest first for better shelf packing
        items   = sorted(self._items, key=lambda x: x[1].get_height(), reverse=True)

        # First pass: compute needed size
        regions: dict[str, pygame.Rect] = {}
        x, y, shelf_h = pad, pad, 0
        atlas_w = self._max_size

        for name, surf in items:
            sw, sh = surf.get_size()
            if x + sw + pad > atlas_w:
                x  = pad
                y += shelf_h + pad
                shelf_h = 0
            if y + sh + pad > self._max_size:
                raise ValueError(
                    f"Sprites do not fit in {self._max_size}×{self._max_size} atlas. "
                    f"Increase max_size or reduce sprite count."
                )
            regions[name] = pygame.Rect(x, y, sw, sh)
            x        += sw + pad
            shelf_h   = max(shelf_h, sh)

        atlas_h = y + shelf_h + pad

        # Create atlas surface and blit all sprites
        atlas = pygame.Surface((atlas_w, atlas_h), pygame.SRCALPHA)
        atlas.fill((0, 0, 0, 0))

        for name, surf in items:
            atlas.blit(surf, regions[name].topleft)

        return SpriteAtlas(atlas, regions)

    def save(
        self,
        image_path: Path,
        meta_path:  Path,
    ) -> SpriteAtlas:
        """
        Build the atlas, save it to disk, and return it.

        Saves:
        - ``image_path`` — the packed PNG image
        - ``meta_path``  — JSON metadata with sprite regions

        Args:
            image_path: Output path for the PNG.
            meta_path:  Output path for the JSON metadata.

        Returns:
            The built ``SpriteAtlas``.
        """
        atlas = self.build()

        image_path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(atlas.surface, str(image_path))

        meta = {
            "size": {"w": atlas.size[0], "h": atlas.size[1]},
            "regions": {
                name: {"x": r.x, "y": r.y, "w": r.width, "h": r.height}
                for name, r in atlas._regions.items()
            },
        }
        meta_path.write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )
        return atlas

    @property
    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()
