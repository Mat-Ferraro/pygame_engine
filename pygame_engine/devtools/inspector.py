"""
Widget and scene tree inspector for pygame_engine.

Dumps a readable text representation of the current scene stack and
widget tree to the debug log. Triggered by the INSPECTOR_TOGGLE action
(F2 by default).

In v1 the inspector is text-based and writes to ``debug_log``.
A visual overlay inspector may follow in a later phase.

Usage::

    from pygame_engine.devtools.inspector import Inspector

    inspector = Inspector()

    # In event handling (when F2 is pressed):
    inspector.dump(scene_manager)

    # Or dump to a string directly:
    report = inspector.format_scene_stack(scene_manager)
    return report  # was print() — callers display the report
"""

from __future__ import annotations

from pygame_engine.devtools.debug_log import log


class Inspector:
    """
    Reads and formats engine state for debug inspection.

    Writes output to ``debug_log`` and optionally returns it as a string.
    """

    def dump(self, scene_manager: object | None = None) -> None:
        """
        Dump a full inspection report to the debug log.

        Args:
            scene_manager: The active SceneManager, or None.
        """
        log("── Inspector dump ──────────────────────", tag="inspector")
        for line in self.format_scene_stack(scene_manager).splitlines():
            log(line, tag="inspector")
        for line in self.format_flags().splitlines():
            log(line, tag="inspector")

    def format_scene_stack(
        self,
        scene_manager: object | None,
    ) -> str:
        """
        Return a formatted string describing the current scene stack.

        Args:
            scene_manager: The active SceneManager, or None.

        Returns:
            Multi-line string representation of the scene stack.
        """
        if scene_manager is None:
            return "SceneManager: None"

        stack = getattr(scene_manager, "_stack", None)
        if stack is None:
            return "SceneManager: no stack"

        scenes = getattr(stack, "_stack", [])
        if not scenes:
            return "SceneStack: empty"

        lines = [f"SceneStack ({len(scenes)} scenes, top→bottom):"]
        for i, scene in enumerate(reversed(scenes)):
            name = type(scene).__name__
            bi   = "↕" if scene.blocks_input_below  else " "
            bu   = "↑" if scene.blocks_update_below else " "
            br   = "●" if scene.blocks_render_below else " "
            rw   = f" root={type(scene.root_widget).__name__}" \
                   if scene.root_widget else ""
            lines.append(f"  [{i}] {name}  i{bi} u{bu} r{br}{rw}")

        return "\n".join(lines)

    def format_flags(self) -> str:
        """Return a formatted string of the current runtime flags."""
        from pygame_engine.state.runtime_flags import flags
        parts = [f"{k}={v}" for k, v in flags.as_dict().items()]
        return "Flags: " + "  ".join(parts)

    def format_widget_tree(
        self,
        widget: object | None,
        depth:  int = 0,
    ) -> str:
        """
        Return a formatted widget tree string starting from ``widget``.

        Args:
            widget: A Widget instance (or None).
            depth:  Current indentation depth (used in recursion).

        Returns:
            Multi-line string representation of the widget tree.
        """
        if widget is None:
            return "(no root widget)"

        indent = "  " * depth
        name   = type(widget).__name__
        rect   = getattr(widget, "rect", None)
        vis    = "" if getattr(widget, "visible", True) else " [hidden]"
        ena    = "" if getattr(widget, "enabled", True) else " [disabled]"
        rect_s = f" {rect.x},{rect.y} {rect.width}×{rect.height}" \
                 if rect else ""

        lines = [f"{indent}{name}{rect_s}{vis}{ena}"]

        children = getattr(widget, "_children", [])
        for child in children:
            lines.append(self.format_widget_tree(child, depth + 1))

        return "\n".join(lines)