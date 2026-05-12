"""
app/config.py

Runtime configuration for the Application.

AppConfig is a plain dataclass — it holds values, owns no logic.
Application reads from it during startup; nothing else should mutate it
after the app is running.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    """
    All configuration an Application needs to initialise itself.

    Fields are grouped by concern: window, timing, display, paths, dev tools.
    Every field has a sensible default so callers only specify what differs.

    Usage::

        config = AppConfig(title="My Game", width=1280, height=720)
        app = Application(config)
        app.run(initial_scene)
    """

    # ── Window ────────────────────────────────────────────────────────────────

    title: str = "pygame_engine"
    """Window title / caption."""

    width: int = 1280
    """Initial window width in pixels."""

    height: int = 720
    """Initial window height in pixels."""

    resizable: bool = False
    """Whether the window can be resized by the user."""

    fullscreen: bool = False
    """Start in fullscreen mode."""

    # ── Timing ────────────────────────────────────────────────────────────────

    target_fps: int = 60
    """Target frame rate. Passed to the pygame clock each frame."""

    max_dt: float = 0.1
    """
    Maximum delta-time value in seconds (clamp guard).

    Prevents huge dt spikes after the window is moved, a breakpoint is hit,
    or the OS suspends the process. 0.1 s ≈ dropping to 10 FPS before clamping.
    Set to 0 to disable clamping.
    """

    # ── Display ───────────────────────────────────────────────────────────────

    vsync: bool = False
    """Enable vsync. Passed as a display flag to pygame."""

    # ── Paths ─────────────────────────────────────────────────────────────────

    asset_root: Path = field(default_factory=lambda: Path("assets"))
    """
    Root directory for project assets.

    Relative paths are resolved from the working directory at startup.
    Override this in game projects to point at the game's asset folder.
    """

    # ── Dev / debug ───────────────────────────────────────────────────────────

    debug: bool = False
    """
    Enable debug mode.

    When True the Application will activate debug overlays and
    verbose logging. Has no effect on release builds that strip debug tools.
    """
