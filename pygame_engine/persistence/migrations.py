"""
persistence/migrations.py

Save version migration infrastructure for pygame_engine.

The engine defines the migration pipeline structure. The game project
registers version-specific handlers that transform old save data into
the current schema.

How it works
------------
1. A save is loaded with a ``save_version`` field in its envelope.
2. The game registers migration handlers: one per version step.
3. ``MigrationRunner.run(data)`` applies each handler in sequence until
   the data is at the current version.

Usage (in a game project)::

    from pygame_engine.persistence.migrations import MigrationRunner

    migrations = MigrationRunner(current_version=3)

    @migrations.register(from_version=1)
    def v1_to_v2(data: dict) -> dict:
        # Rename a field that changed between versions 1 and 2
        data["payload"]["health_points"] = data["payload"].pop("hp", 100)
        return data

    @migrations.register(from_version=2)
    def v2_to_v3(data: dict) -> dict:
        # Add a new field that didn't exist in version 2
        data["payload"].setdefault("stamina", 100)
        return data

    # When loading a save:
    raw = storage.read(path)
    migrated = migrations.run(raw)   # runs v1→v2→v3 if needed
"""

from __future__ import annotations

from typing import Any, Callable


MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


class MigrationError(Exception):
    """Raised when a migration step fails."""


class MigrationRunner:
    """
    Runs a chain of version migration handlers on save data.

    Register handlers with ``@runner.register(from_version=N)``.
    Call ``runner.run(data)`` when loading a save to bring it up to
    the current version automatically.
    """

    def __init__(self, current_version: int) -> None:
        """
        Args:
            current_version: The schema version the game currently expects.
                             Saves already at this version are returned
                             unchanged by ``run()``.
        """
        self._current_version = current_version
        self._handlers: dict[int, MigrationFn] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        from_version: int,
    ) -> Callable[[MigrationFn], MigrationFn]:
        """
        Decorator — register a migration handler for a specific version step.

        The handler receives the full save envelope dict (including
        ``save_version`` and ``payload``) and must return it modified.
        It should increment ``save_version`` to reflect the step it just
        applied.

        Args:
            from_version: The save version this handler upgrades FROM.

        Example::

            @migrations.register(from_version=1)
            def v1_to_v2(data):
                data["payload"]["new_field"] = "default"
                data["save_version"] = 2
                return data
        """
        def decorator(fn: MigrationFn) -> MigrationFn:
            if from_version in self._handlers:
                raise ValueError(
                    f"Migration handler for version {from_version} already registered."
                )
            self._handlers[from_version] = fn
            return fn
        return decorator

    def register_fn(self, from_version: int, fn: MigrationFn) -> None:
        """
        Register a migration handler without using the decorator syntax.

        Args:
            from_version: The save version this handler upgrades FROM.
            fn:           The migration function.
        """
        if from_version in self._handlers:
            raise ValueError(
                f"Migration handler for version {from_version} already registered."
            )
        self._handlers[from_version] = fn

    # ── Running ───────────────────────────────────────────────────────────────

    def run(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Apply all necessary migration steps to bring ``data`` to the
        current version.

        Steps are applied in ascending version order. If the data is
        already at the current version it is returned unchanged.

        Args:
            data: The raw save envelope dict as loaded from disk.
                  Must contain a ``"save_version"`` key.

        Returns:
            The migrated save envelope dict.

        Raises:
            MigrationError: If a required migration handler is not
                            registered or a handler raises an exception.
            KeyError:       If ``data`` has no ``"save_version"`` field.
        """
        version: int = data["save_version"]

        while version < self._current_version:
            if version not in self._handlers:
                raise MigrationError(
                    f"No migration handler registered for save_version={version}. "
                    f"Cannot upgrade to version {self._current_version}."
                )
            try:
                data = self._handlers[version](data)
            except Exception as exc:
                raise MigrationError(
                    f"Migration from version {version} failed: {exc}"
                ) from exc
            version = data.get("save_version", version + 1)

        return data

    def needs_migration(self, data: dict[str, Any]) -> bool:
        """
        Return True if ``data`` is at an older version than current.

        Args:
            data: Save envelope dict with a ``"save_version"`` key.
        """
        return int(data.get("save_version", 0)) < self._current_version

    @property
    def current_version(self) -> int:
        """The current expected save version."""
        return self._current_version

    @property
    def registered_versions(self) -> list[int]:
        """Sorted list of from-versions that have registered handlers."""
        return sorted(self._handlers)
