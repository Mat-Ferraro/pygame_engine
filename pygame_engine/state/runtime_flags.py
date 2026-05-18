"""
``RuntimeFlags`` holds a small set of named boolean switches that
control engine behaviour at runtime. Each flag has a clear, specific
purpose. This is not a general-purpose key-value store.

A module-level singleton ``flags`` is provided for convenience.
``Application`` resets it to defaults on startup so each run begins
clean.

Usage::

    from pygame_engine.state.runtime_flags import flags

    # Read
    if flags.debug:
        draw_debug_overlay(surface)

    # Set
    flags.debug = True
    flags.show_rects = True

    # Toggle
    flags.toggle("show_fps")

    # Reset all to defaults
    flags.reset()

Adding game-specific flags
--------------------------
Game projects should not add flags to this class directly.
Instead, create a separate flags object in the game project:

    # game/flags.py
    from pygame_engine.state.runtime_flags import RuntimeFlags

    class GameFlags(RuntimeFlags):
        def __init__(self) -> None:
            super().__init__()
            self.show_hitboxes: bool = False
            self.god_mode:      bool = False

    game_flags = GameFlags()
"""

from __future__ import annotations


class RuntimeFlags:
    """
    Named boolean runtime flags for the engine.

    All flags default to False. They are reset to False by
    ``Application._startup()`` at the start of each run.

    Engine flags
    ------------
    debug        — global debug mode (enables all debug subsystems)
    show_fps     — display FPS counter in window title or overlay
    show_rects   — draw widget/scene rects as coloured outlines
    show_overlay — display the debug overlay panel
    show_console — display the debug console log panel
    """

    def __init__(self) -> None:
        self.debug:        bool = False
        """Master debug switch. Enables all debug subsystems when True."""

        self.show_fps:     bool = False
        """Show FPS counter. Enabled automatically when debug=True."""

        self.show_rects:   bool = False
        """Draw bounding rects for all widgets and scenes."""

        self.show_overlay: bool = False
        """Show the debug overlay panel."""

        self.show_console: bool = False
        """Show the debug console log panel."""

    # ── Convenience ───────────────────────────────────────────────────────────

    def toggle(self, name: str) -> bool:
        """
        Toggle a named flag and return its new value.

        Args:
            name: The attribute name of the flag to toggle.

        Returns:
            The new value of the flag after toggling.

        Raises:
            AttributeError: If ``name`` is not a known flag.
        """
        if not hasattr(self, name):
            raise AttributeError(
                f"RuntimeFlags has no flag '{name}'. "
                f"Known flags: {self._flag_names()}"
            )
        new_value = not getattr(self, name)
        setattr(self, name, new_value)
        return new_value

    def reset(self) -> None:
        """Reset all flags to their default values (False)."""
        self.__init__()  # type: ignore[misc]

    def enable_debug_all(self) -> None:
        """Enable debug mode and all debug display flags."""
        self.debug        = True
        self.show_fps     = True
        self.show_rects   = True
        self.show_overlay = True
        self.show_console = True

    def as_dict(self) -> dict[str, bool]:
        """Return all flags as a plain dict."""
        return {name: getattr(self, name) for name in self._flag_names()}

    # ── Internal ──────────────────────────────────────────────────────────────

    def _flag_names(self) -> list[str]:
        return [k for k in vars(self) if not k.startswith("_")]

    def __repr__(self) -> str:
        flags = ", ".join(
            f"{k}={v}" for k, v in self.as_dict().items() if v
        )
        return f"RuntimeFlags({flags or 'all False'})"


# Module-level singleton — the engine's shared flag instance.
# Application resets this at startup.
flags: RuntimeFlags = RuntimeFlags()