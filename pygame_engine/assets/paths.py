"""
assets/paths.py

Canonical asset path resolution for pygame_engine.

All file path logic lives here. Nothing else in the engine should
construct asset paths manually — go through these helpers instead.

The asset root is set from ``AppConfig.asset_root`` at startup and
stored on the ``AssetLoader`` instance. ``PathResolver`` is a small
helper that ``AssetLoader`` uses internally.

Folder conventions (recommended, not enforced):
    assets/
    ├── fonts/
    ├── images/
    │   ├── ui/
    │   └── sprites/
    └── sounds/
"""

from __future__ import annotations

from pathlib import Path


class PathResolver:
    """
    Resolves asset paths relative to a configured root directory.

    Owned by ``AssetLoader``. Created once at startup with the
    ``asset_root`` from ``AppConfig``.
    """

    def __init__(self, asset_root: Path) -> None:
        self._root = asset_root.resolve()

    # ── Resolution ────────────────────────────────────────────────────────────

    def resolve(self, relative: str | Path) -> Path:
        """
        Resolve a relative asset path to an absolute path.

        Args:
            relative: Path relative to the asset root.

        Returns:
            Absolute ``Path``.
        """
        return (self._root / relative).resolve()

    def font(self, relative: str | Path) -> Path:
        """Resolve a path inside the ``fonts/`` subdirectory."""
        return self.resolve(Path("fonts") / relative)

    def image(self, relative: str | Path) -> Path:
        """Resolve a path inside the ``images/`` subdirectory."""
        return self.resolve(Path("images") / relative)

    def sound(self, relative: str | Path) -> Path:
        """Resolve a path inside the ``sounds/`` subdirectory."""
        return self.resolve(Path("sounds") / relative)

    # ── Validation ────────────────────────────────────────────────────────────

    def exists(self, relative: str | Path) -> bool:
        """Return True if the resolved path exists on disk."""
        return self.resolve(relative).exists()

    @property
    def root(self) -> Path:
        """The resolved asset root directory."""
        return self._root
