"""
ConfirmDialog — modal overlay scene for destructive action confirmation.

Presents a centred dialog over a dimmed background asking the user to
confirm or cancel an action. The dialog pushes itself onto the scene
stack and pops when the user responds.

ConfirmDialog is intentionally NOT a subclass of Scene — doing so would
create a circular import (scene → ui.Widget → ui.__init__ → ConfirmDialog
→ scene). Instead it implements the Scene protocol (handle_event, update,
render, on_enter) and is wrapped in a lightweight adapter when pushed.

Usage — push from any scene::

    from pygame_engine.ui.feedback.confirm_dialog import ConfirmDialog

    def _on_release_hero(self) -> None:
        ConfirmDialog.push(
            app=self._app,
            message=f"Release {hero.name} from the guild?",
            confirm_label="Release",
            on_confirm=self._do_release,
        )

The dialog pops itself automatically after the user responds.
"""

from __future__ import annotations

from typing import Callable

import pygame

from pygame_engine.graphics.draw_utils import draw_rect_bordered
from pygame_engine.graphics.surfaces import make_alpha_surface, blit_alpha_surface
from pygame_engine.theme.runtime import get_theme


class ConfirmDialog:
    """
    Modal confirmation overlay implementing the Scene protocol.

    Does NOT subclass Scene to avoid circular imports.
    Use ``ConfirmDialog.push()`` to add it to the scene stack.

    Args:
        app:            The running Application instance.
        message:        Question to display (supports \\n newlines).
        confirm_label:  Label for the confirm button. Default ``"Confirm"``.
        cancel_label:   Label for the cancel button. Default ``"Cancel"``.
        on_confirm:     Called with no arguments when confirmed.
        on_cancel:      Called with no arguments when cancelled (or Escape).
        danger:         If True, the confirm button uses the danger (red) style.
    """

    DIALOG_W = 480
    DIALOG_H = 220

    def __init__(
        self,
        app,
        message:       str,
        confirm_label: str = "Confirm",
        cancel_label:  str = "Cancel",
        on_confirm:    Callable[[], None] | None = None,
        on_cancel:     Callable[[], None] | None = None,
        danger:        bool = True,
    ) -> None:
        self._app           = app
        self._message       = message
        self._confirm_label = confirm_label
        self._cancel_label  = cancel_label
        self._on_confirm    = on_confirm
        self._on_cancel     = on_cancel
        self._danger        = danger

        self._confirm_hovered = False
        self._cancel_hovered  = False
        self._overlay_surf:  pygame.Surface | None = None
        self._overlay_size:  tuple[int, int]        = (0, 0)

    # ── Class-level factory ───────────────────────────────────────────────────

    @classmethod
    def push(
        cls,
        app,
        message:       str,
        confirm_label: str = "Confirm",
        cancel_label:  str = "Cancel",
        on_confirm:    Callable[[], None] | None = None,
        on_cancel:     Callable[[], None] | None = None,
        danger:        bool = True,
    ) -> "ConfirmDialog":
        """
        Create a ConfirmDialog and push it onto the scene stack.

        Wraps the dialog in a thin Scene adapter so the engine's scene
        manager can drive it without a circular import.
        """
        dialog = cls(
            app=app,
            message=message,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
            on_confirm=on_confirm,
            on_cancel=on_cancel,
            danger=danger,
        )

        # Lazy Scene import — only runs after all modules are loaded.
        from pygame_engine.scene.scene import Scene  # noqa: PLC0415

        class _Adapter(Scene):
            """Thin Scene wrapper that delegates to the ConfirmDialog."""
            def __init__(self_, dlg):
                super().__init__()
                self_._dlg = dlg

            def on_enter(self_):
                pass

            def _handle_event_scene(self_, event):
                return self_._dlg._handle_event(event)

            def update(self_, dt):
                super().update(dt)

            def render(self_, surface):
                self_._dlg._render(surface)
                super().render(surface)

        app.scene_manager.push(_Adapter(dialog))
        return dialog

    # ── Scene protocol (called via _Adapter) ──────────────────────────────────

    def _handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._do_cancel()
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._do_confirm()
                return True

        if event.type == pygame.MOUSEMOTION:
            conf_r, canc_r = self._button_rects()
            self._confirm_hovered = conf_r.collidepoint(event.pos)
            self._cancel_hovered  = canc_r.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            conf_r, canc_r = self._button_rects()
            if conf_r.collidepoint(event.pos):
                self._do_confirm()
                return True
            if canc_r.collidepoint(event.pos):
                self._do_cancel()
                return True

        return False

    def _render(self, surface: pygame.Surface) -> None:
        sw, sh = surface.get_size()

        # Dim overlay
        if self._overlay_surf is None or self._overlay_size != (sw, sh):
            self._overlay_surf = make_alpha_surface(sw, sh)
            self._overlay_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(self._overlay_surf, (0, 0, 0, 160),
                             pygame.Rect(0, 0, sw, sh))
            self._overlay_size = (sw, sh)
        blit_alpha_surface(surface, self._overlay_surf, (0, 0), 1.0)

        # Dialog panel
        theme = get_theme()
        dlg_r = self._dialog_rect(sw, sh)
        draw_rect_bordered(
            surface, dlg_r,
            fill=theme.colours.bg_raised,
            border=theme.colours.border,
            radius=theme.panel.surface.radius,
        )

        # Message text
        font_md = pygame.font.SysFont(theme.typography.family, theme.typography.md)
        font_sm = pygame.font.SysFont(theme.typography.family, theme.typography.sm)
        pad     = 28
        msg_x   = dlg_r.x + pad
        msg_y   = dlg_r.y + pad

        for line in self._message.splitlines():
            lsurf = font_md.render(line, True, theme.colours.text)
            surface.blit(lsurf, (msg_x, msg_y))
            msg_y += font_md.get_linesize() + 4

        # Confirm button
        conf_r, canc_r = self._button_rects()
        conf_bg = (130, 40, 40) if self._danger else theme.button.normal.bg
        if self._confirm_hovered:
            conf_bg = (170, 55, 55) if self._danger else theme.button.hovered.bg
        draw_rect_bordered(surface, conf_r, fill=conf_bg,
                           border=theme.colours.border, radius=6)
        csurf = font_sm.render(self._confirm_label, True, theme.colours.text)
        surface.blit(csurf, csurf.get_rect(center=conf_r.center))

        # Cancel button
        canc_bg = theme.button.hovered.bg if self._cancel_hovered else theme.button.normal.bg
        draw_rect_bordered(surface, canc_r, fill=canc_bg,
                           border=theme.colours.border, radius=6)
        xsurf = font_sm.render(self._cancel_label, True, theme.colours.text)
        surface.blit(xsurf, xsurf.get_rect(center=canc_r.center))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _dialog_rect(self, sw: int, sh: int) -> pygame.Rect:
        return pygame.Rect(
            (sw - self.DIALOG_W) // 2,
            (sh - self.DIALOG_H) // 2,
            self.DIALOG_W,
            self.DIALOG_H,
        )

    def _button_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        if hasattr(self._app, "screen"):
            sw, sh = self._app.screen.get_size()
        else:
            sw, sh = 1920, 1080
        dlg   = self._dialog_rect(sw, sh)
        btn_h = 40
        btn_w = 160
        pad   = 28
        y     = dlg.bottom - btn_h - pad
        conf  = pygame.Rect(dlg.right - pad - btn_w, y, btn_w, btn_h)
        canc  = pygame.Rect(conf.left - 12 - btn_w,  y, btn_w, btn_h)
        return conf, canc

    def _do_confirm(self) -> None:
        self._app.scene_manager.pop()
        if self._on_confirm:
            self._on_confirm()

    def _do_cancel(self) -> None:
        self._app.scene_manager.pop()
        if self._on_cancel:
            self._on_cancel()
