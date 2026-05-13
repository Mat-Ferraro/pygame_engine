"""
Demonstrates SpriteAtlas packing and LocaleStore with runtime language switching.

What this example shows:
- Building an AtlasPacker from plain-colour surfaces at startup
- Blitting named sprites from the packed atlas by name
- LocaleStore loaded with English and French dicts
- Language switching at runtime with L key — all labels update instantly
- Plural form translation (count.item)

Controls:
    L   — switch language (EN ↔ FR)
    ESC — quit

Run from the repo root:
    python -m examples.example_atlas_locale
"""

from __future__ import annotations

import pygame

from pygame_engine.app import Application, AppConfig
from pygame_engine.atlas import AtlasPacker, SpriteAtlas
from pygame_engine.input import actions
from pygame_engine.layout import anchor
from pygame_engine.locale import LocaleStore
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Label, Panel, Stack

# ── Locale data ───────────────────────────────────────────────────────────────

EN = {
    "title":         "Sprite Atlas + Localisation Demo",
    "hint":          "Press L to switch language  •  ESC to quit",
    "sprite.player": "Player",
    "sprite.coin":   "Coin",
    "sprite.enemy":  "Enemy",
    "sprite.gem":    "Gem",
    "count.item":    {"one": "{count} item", "other": "{count} items"},
    "atlas_info":    "Atlas: {w}×{h}px  •  {n} sprites packed",
}
FR = {
    "title":         "Démo Atlas de Sprites + Localisation",
    "hint":          "Appuyez sur L pour changer de langue  •  ESC pour quitter",
    "sprite.player": "Joueur",
    "sprite.coin":   "Pièce",
    "sprite.enemy":  "Ennemi",
    "sprite.gem":    "Gemme",
    "count.item":    {"one": "{count} élément", "other": "{count} éléments"},
    "atlas_info":    "Atlas: {w}×{h}px  •  {n} sprites emballés",
}

# ── Sprite definitions ────────────────────────────────────────────────────────

SPRITES = [
    ("sprite.player", (80,  140, 220), (48, 48)),
    ("sprite.coin",   (210, 170,  40), (32, 32)),
    ("sprite.enemy",  (200,  60,  60), (36, 36)),
    ("sprite.gem",    (100, 200, 160), (28, 28)),
]


def _build_atlas() -> SpriteAtlas:
    packer = AtlasPacker(max_size=512, padding=2)
    for key, colour, size in SPRITES:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(colour)
        pygame.draw.rect(surf, tuple(min(255, c + 50) for c in colour),
                         surf.get_rect(), width=2)
        packer.add(key, surf)
    return packer.build()


# ── Scene ─────────────────────────────────────────────────────────────────────

class AtlasLocaleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app   = app
        self._atlas: SpriteAtlas | None = None
        self._store = LocaleStore(fallback_locale="en")
        self._store.load_dict(EN, locale="en")
        self._store.load_dict(FR, locale="fr")
        self._store.set_locale("en")

        # Mutable labels updated on language switch
        self._title_lbl:  Label | None = None
        self._info_lbl:   Label | None = None
        self._count_lbl:  Label | None = None
        self._hint_lbl:   Label | None = None
        self._name_lbls:  list[Label] = []

        # Sprite blit positions — computed in on_enter, used in render
        self._sprite_positions: list[tuple[str, tuple[int, int]]] = []

    def on_enter(self) -> None:
        self._atlas = _build_atlas()
        self._build_ui(self._app.screen_rect)

    def on_resize(self, width: int, height: int) -> None:
        self._build_ui(pygame.Rect(0, 0, width, height))

    def _build_ui(self, screen: pygame.Rect) -> None:
        t     = self._store.t
        theme = get_theme()
        atlas = self._atlas
        aw, ah = atlas.size if atlas else (0, 0)
        n      = atlas.count if atlas else 0

        ROW_H  = 56   # height per sprite row
        ROWS   = len(SPRITES)
        TABLE_H = ROWS * ROW_H
        PANEL_W = 480
        PANEL_H = TABLE_H + 80   # padding top + bottom

        panel_rect = anchor(screen, (PANEL_W, PANEL_H), "center")
        panel      = Panel(panel_rect)

        # ── Title ─────────────────────────────────────────────────────────────
        self._title_lbl = Label(
            pygame.Rect(panel_rect.x, panel_rect.y - 52,
                        panel_rect.width, 40),
            t("title"),
            font_size=theme.typography.lg,
            colour=theme.colours.text, align="center",
        )

        # ── Atlas info + count ────────────────────────────────────────────────
        info_y = panel_rect.y + 16
        self._info_lbl = Label(
            pygame.Rect(panel_rect.x + 16, info_y, panel_rect.width - 32, 22),
            t("atlas_info", w=aw, h=ah, n=n),
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary, align="center",
        )
        self._count_lbl = Label(
            pygame.Rect(panel_rect.x + 16, info_y + 26, panel_rect.width - 32, 20),
            t("count.item", count=n),
            font_size=theme.typography.sm,
            colour=theme.colours.text_secondary, align="center",
        )
        panel.add(self._info_lbl)
        panel.add(self._count_lbl)

        # ── Sprite rows — icon column + name column ───────────────────────────
        # icon at x = panel_left + 32
        # name label starts after icon area
        ICON_X   = panel_rect.x + 32
        ICON_COL = 64   # space reserved for the icon
        NAME_X   = ICON_X + ICON_COL
        NAME_W   = panel_rect.width - ICON_COL - 48

        table_top = panel_rect.y + 72
        self._name_lbls = []
        self._sprite_positions = []

        for i, (key, colour, size) in enumerate(SPRITES):
            row_y  = table_top + i * ROW_H
            icon_y = row_y + (ROW_H - size[1]) // 2

            # Record where to blit the sprite in render()
            self._sprite_positions.append((key, (ICON_X, icon_y)))

            # Name label — vertically centred in row
            lbl = Label(
                pygame.Rect(NAME_X, row_y, NAME_W, ROW_H),
                t(key),
                font_size=theme.typography.md,
                colour=theme.colours.text, align="left",
            )
            self._name_lbls.append(lbl)
            panel.add(lbl)

        # ── Hint ──────────────────────────────────────────────────────────────
        self._hint_lbl = Label(
            anchor(screen, (600, 22), "bottom", margin=14),
            t("hint"),
            font_size=theme.typography.xs,
            colour=theme.colours.text_secondary, align="center",
        )

        root = Stack(pygame.Rect(screen))
        root.add(panel)
        root.add(self._title_lbl)
        root.add(self._hint_lbl)
        self.root_widget = root

    def _refresh_labels(self) -> None:
        t     = self._store.t
        atlas = self._atlas
        aw, ah = atlas.size if atlas else (0, 0)
        n      = atlas.count if atlas else 0

        if self._title_lbl:  self._title_lbl.text  = t("title")
        if self._info_lbl:   self._info_lbl.text    = t("atlas_info", w=aw, h=ah, n=n)
        if self._count_lbl:  self._count_lbl.text   = t("count.item", count=n)
        if self._hint_lbl:   self._hint_lbl.text    = t("hint")
        for i, (key, _, _) in enumerate(SPRITES):
            if i < len(self._name_lbls):
                self._name_lbls[i].text = t(key)

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            loc = "fr" if self._store.active_locale == "en" else "en"
            self._store.set_locale(loc)
            self._refresh_labels()
            return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(get_theme().colours.bg_base)
        super().render(surface)   # draws panel + labels

        # Blit atlas sprites on top (over the panel background, under nothing)
        if self._atlas:
            for key, pos in self._sprite_positions:
                self._atlas.blit(surface, key, pos)


def run() -> None:
    app = Application(AppConfig(
        title="pygame_engine — atlas + locale",
        width=1280, height=720,
        resizable=True,
    ))
    app.run(AtlasLocaleScene(app))


if __name__ == "__main__":
    run()
