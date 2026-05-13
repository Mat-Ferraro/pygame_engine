"""
game/ui/

Game-specific composite widgets built from engine primitives.

Examples of what belongs here:
- HealthBar       — shows player HP using ProgressBar
- MiniMap         — small map widget
- InventoryPanel  — grid of item slots built from Panel + Button
- DialogueBox     — NPC dialogue display using TextBlock
- HUDOverlay      — combines multiple HUD elements

Rules:
- Subclass engine widgets (Panel, Widget, Stack)
- Use engine layout helpers for positioning
- Read theme values via get_theme()
- Do NOT contain gameplay logic — only presentation

Example::

    from pygame_engine.ui import ProgressBar
    from pygame_engine.theme.runtime import get_theme

    class HealthBar(ProgressBar):
        def __init__(self, rect):
            super().__init__(rect, fill_colour=(220, 60, 60))

        def update_from_player(self, player) -> None:
            self.value = player.health / player.max_health
"""
