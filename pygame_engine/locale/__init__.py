"""
pygame_engine.locale

Lightweight string localisation for pygame_engine games.

The engine renders strings it's given. This module determines which
strings get passed — it is a pure lookup layer with no pygame dependency.

Public API::

    from pygame_engine.locale import LocaleStore

    store = LocaleStore()
    store.load_file(Path("game/locale/en.json"), locale="en")
    store.load_file(Path("game/locale/fr.json"), locale="fr")
    store.set_locale("en")

    # Simple lookup
    text = store.t("menu.start")

    # With substitution
    text = store.t("hud.score", value=1234)

    # With pluralisation
    text = store.t("item.apple", count=3)

    # Convenience: bind t() as a module-level shortcut in your game
    from game.locale import t   # your game's wrapper
"""

from pygame_engine.locale.locale_store import LocaleStore

__all__ = ["LocaleStore"]
