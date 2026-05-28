"""
Usage — wrap your entry point::

    from pygame_engine.devtools.crash_log import install_crash_handler

    install_crash_handler(Path("crash.log"))   # call once before app.run()
    app.run(MainMenuScene(app))

Or use the context manager::

    from pygame_engine.devtools.crash_log import crash_guard

    with crash_guard(Path("crash.log")):
        app.run(MainMenuScene(app))

The crash report contains:
- ISO timestamp
- Python and pygame-ce version
- Platform info
- Full traceback
- Last 50 debug log entries (if any)
"""

from __future__ import annotations

import platform
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def write_crash_report(path: Path, exc: BaseException) -> None:
    """Write a structured crash report to disk and return the log file path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("pygame_engine CRASH REPORT")
    lines.append("=" * 60)
    lines.append(f"Time:     {datetime.now().isoformat()}")
    lines.append(f"Python:   {sys.version}")
    lines.append(f"Platform: {platform.platform()}")
    try:
        import pygame
        lines.append(f"pygame:   {pygame.version.ver}")
    except Exception:
        lines.append("pygame:   unknown")
    lines.append("")
    lines.append("── Traceback ──────────────────────────────────────────────")
    lines.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        from pygame_engine.devtools.debug_log import get_entries
        entries = get_entries(limit=50)
        if entries:
            lines.append("")
            lines.append("── Last debug log entries (newest first) ──────────────")
            for entry in entries:
                lines.append(f"  [{entry.level}] [{entry.tag}] {entry.message}")
    except Exception:
        pass
    lines.append("")
    lines.append("=" * 60)
    path.write_text("\n".join(lines), encoding="utf-8")


def install_crash_handler(log_path: Path = Path("crash.log")) -> None:
    """Install a global exception hook that writes crash reports."""
    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        try:
            write_crash_report(log_path, exc_value)
            # print() to stderr is intentional here — debug_log cannot be used when the
            # engine is in a crash state. This is an explicit exception to LOGGING_STANDARDS.
            print(f"\n[crash_log] Report written to: {log_path}", file=sys.stderr)
        except Exception as e:
            # Same justification — crash context, debug_log unavailable.
            print(f"\n[crash_log] Failed to write report: {e}", file=sys.stderr)
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _hook


@contextmanager
def crash_guard(log_path: Path = Path("crash.log")):
    """Context manager that catches exceptions, writes a crash report, then re-raises."""
    try:
        yield
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        try:
            write_crash_report(log_path, exc)
            # print() to stderr is intentional here — debug_log cannot be used when the
            # engine is in a crash state. This is an explicit exception to LOGGING_STANDARDS.
            print(f"\n[crash_log] Report written to: {log_path}", file=sys.stderr)
        except Exception as write_err:
            print(f"\n[crash_log] Failed to write report: {write_err}", file=sys.stderr)
        raise