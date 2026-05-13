"""
Demonstrates Sprite Atlas and Localisation together.

What this example shows:
- Building an atlas from plain-colour surfaces at startup
- Blitting named sprites from the atlas
- LocaleStore with English and French
- Language switching at runtime

Controls:
    L — switch language (EN / FR)
    ESC — quit

Run from the repo root:
    python -m examples.example_atlas_locale
"""

from __future__ import annotations
import pygame
from pygame_engine.app import Application, AppConfig
from pygame_engine.atlas import AtlasPacker, SpriteAtlas
from pygame_engine.layout import anchor, column
from pygame_engine.locale import LocaleStore
from pygame_engine.scene import Scene
from pygame_engine.theme.runtime import get_theme
from pygame_engine.ui import Button, Label, Panel, Stack

EN = {
    "title":         "Sprite Atlas + Localisation Demo",
    "lang_label":    "Language",
    "hint":          "Press L to switch language  •  ESC to quit",
    "sprite.player": "Player",
    "sprite.coin":   "Coin",
    "sprite.enemy":  "Enemy",
    "sprite.gem":    "Gem",
    "count.item":   {"one": "{count} item", "other": "{count} items"},
    "atlas_info":   "Atlas: {w}×{h}px  •  {n} sprites packed",
}
FR = {
    "title":         "Démo Atlas de Sprites + Localisation",
    "lang_label":    "Langue",
    "hint":          "Appuyez sur L pour changer de langue  •  ESC pour quitter",
    "sprite.player": "Joueur",
    "sprite.coin":   "Pièce",
    "sprite.enemy":  "Ennemi",
    "sprite.gem":    "Gemme",
    "count.item":   {"one": "{count} élément", "other": "{count} éléments"},
    "atlas_info":   "Atlas: {w}×{h}px  •  {n} sprites emballés",
}

SPRITE_COLOURS = {
    "player": (80, 140, 220),
    "coin":   (210, 170, 40),
    "enemy":  (200, 60, 60),
    "gem":    (100, 200, 160),
}


def build_atlas() -> SpriteAtlas:
    packer = AtlasPacker(max_size=256, padding=2)
    for name, colour in SPRITE_COLOURS.items():
        size = (48, 48) if name == "player" else (32, 32)
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(colour)
        pygame.draw.rect(surf, tuple(min(255, c+40) for c in colour),
                         surf.get_rect(), width=2)
        packer.add(f"sprite.{name}", surf)
    return packer.build()


class AtlasLocaleScene(Scene):

    def __init__(self, app: Application) -> None:
        super().__init__()
        self._app    = app
        self._atlas: SpriteAtlas | None = None
        self._store  = LocaleStore(fallback_locale="en")
        self._store.load_dict(EN, locale="en")
        self._store.load_dict(FR, locale="fr")
        self._store.set_locale("en")
        self._labels: dict[str, Label] = {}

    def on_enter(self) -> None:
        self._atlas = build_atlas()
        self._build_ui()

    def _build_ui(self) -> None:
        t      = self._store.t
        screen = self._app.screen_rect
        theme  = get_theme()
        atlas  = self._atlas
        aw, ah = atlas.size if atlas else (0, 0)
        n      = atlas.count if atlas else 0

        root  = Stack(pygame.Rect(screen))
        panel = Panel(anchor(screen, (600, 400), "center"))

        rows  = column(panel.rect, count=6, item_size=(520, 52), spacing=8,
                       padding=theme.spacing.xl)

        def lbl(rect, key, **kw):
            l = Label(rect, t(key, **kw), font_size=theme.typography.md,
                      colour=theme.colours.text, align="center")
            self._labels[key] = l
            return l

        # Title
        title_rect = pygame.Rect(panel.rect.x, panel.rect.y - 56,
                                 panel.rect.width, 44)
        self._labels["title"] = Label(title_rect, t("title"),
                                      font_size=theme.typography.lg,
                                      colour=theme.colours.text, align="center")

        # Atlas info
        self._labels["atlas_info"] = Label(rows[0], t("atlas_info", w=aw, h=ah, n=n),
                                           font_size=theme.typography.sm,
                                           colour=theme.colours.text_secondary,
                                           align="center")

        # Sprite names
        for i, name in enumerate(SPRITE_COLOURS, 2):
            key = f"sprite.{name}"
            self._labels[key] = Label(rows[i], t(key),
                                      font_size=theme.typography.sm,
                                      colour=theme.colours.text, align="center")
            panel.add(self._labels[key])

        # Count demo
        self._labels["count.item"] = Label(rows[1], t("count.item", count=n),
                                           font_size=theme.typography.sm,
                                           colour=theme.colours.text_secondary,
                                           align="center")
        panel.add(self._labels["count.item"])
        panel.add(self._labels["atlas_info"])

        # Hint
        hint = Label(pygame.Rect(panel.rect.x, panel.rect.bottom + 12,
                                 panel.rect.width, 28),
                     t("hint"), font_size=theme.typography.xs,
                     colour=theme.colours.text_secondary, align="center")
        self._labels["hint"] = hint

        root.add(panel)
        root.add(self._labels["title"])
        root.add(hint)
        self.root_widget = root

    def _refresh_labels(self) -> None:
        t = self._store.t
        atlas = self._atlas
        aw, ah = atlas.size if atlas else (0, 0)
        n = atlas.count if atlas else 0
        mapping = {
            "title":      t("title"),
            "atlas_info": t("atlas_info", w=aw, h=ah, n=n),
            "count.item": t("count.item", count=n),
            "hint":       t("hint"),
        }
        for name in SPRITE_COLOURS:
            mapping[f"sprite.{name}"] = t(f"sprite.{name}")
        for key, text in mapping.items():
            if key in self._labels:
                self._labels[key].text = text

    def _handle_event_scene(self, event: pygame.event.Event) -> bool:
        from pygame_engine.input import actions
        if self._app.input_manager.was_action_pressed(actions.CANCEL):
            self._app.stop(); return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            current = self._store.active_locale
            self._store.set_locale("fr" if current == "en" else "en")
            self._refresh_labels(); return True
        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((22, 22, 30))
        super().render(surface)

        if not self._atlas:
            return
        # Draw sprites alongside their labels
        screen = self._app.screen_rect
        names  = list(SPRITE_COLOURS.keys())
        start_x = screen.centerx - (len(names) * 80) // 2
        for i, name in enumerate(names):
            key  = f"sprite.{name}"
            lbl  = self._labels.get(key)
            if lbl is None:
                continue
            dest = (start_x + i * 80, lbl.rect.y - 52)
            self._atlas.blit(surface, key, dest)


def run() -> None:
    app = Application(AppConfig(title="pygame_engine — atlas + locale",
                                width=1280, height=720))
    app.run(AtlasLocaleScene(app))

if __name__ == "__main__":
    run()
