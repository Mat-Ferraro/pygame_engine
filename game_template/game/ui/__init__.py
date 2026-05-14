"""
Game-specific composite widgets built from engine primitives.

Phase 14 additions — all available directly from pygame_engine.ui:

    ListView       — scrollable list, custom row_renderer, keyboard nav
    Badge          — coloured pill label (styles: default/info/good/warning/danger)
    IntStepper     — label with − / + buttons for discrete integer values
    LogPanel       — scrollable text log with append() and auto-scroll
    KeyValuePanel  — two-column label:value display panel
    ConfirmDialog  — modal overlay for destructive action confirmation

Usage examples::

    from pygame_engine.ui import ListView, Badge, IntStepper, LogPanel, KeyValuePanel
    from pygame_engine.ui.feedback.confirm_dialog import ConfirmDialog

    # ListView with custom row renderer
    lv = ListView(rect, row_height=56, on_select=self._on_select)
    lv.row_renderer = self._draw_row
    lv.set_items(my_list)

    # Badge
    Badge(pygame.Rect(x, y, 80, 26), "Warrior", style="info").render(surface)

    # IntStepper
    stepper = IntStepper(rect, value=1, min_value=1, max_value=8,
                         label="Campaigns", on_change=self._on_change)

    # LogPanel
    log = LogPanel(rect, max_lines=200)
    log.append("Round resolved.", colour=(180, 230, 180))

    # KeyValuePanel
    kv = KeyValuePanel(rect, title="Hero")
    kv.set_rows([("Name", hero.name), ("Power", hero.combat_power())])

    # ConfirmDialog
    ConfirmDialog.push(
        app=self._app,
        message=f"Release {hero.name}?",
        confirm_label="Release",
        on_confirm=self._do_release,
        danger=True,
    )

Game-specific composite widgets (add your own below):

    from pygame_engine.ui import ProgressBar
    from pygame_engine.theme.runtime import get_theme

    class HealthBar(ProgressBar):
        def __init__(self, rect):
            super().__init__(rect, fill_colour=(220, 60, 60))

        def update_from_player(self, player) -> None:
            self.value = player.health / player.max_health

Rules:
- Subclass engine widgets (Panel, Widget, Stack)
- Use engine layout helpers for positioning
- Read theme values via get_theme()
- Do NOT contain gameplay logic — only presentation
"""
