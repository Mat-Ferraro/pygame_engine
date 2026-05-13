"""
game/locale/__init__.py

Locale setup for MY_GAME.

Usage::

    from game.locale import t

    label.text = t("menu.start")
    label.text = t("hud.score", value=1234)
    label.text = t("item.coin", count=3)
"""

from pathlib import Path
from pygame_engine.locale import LocaleStore

_store = LocaleStore(fallback_locale="en")

def load_locales() -> None:
    """Load all locale files. Call once during app startup."""
    locale_dir = Path(__file__).parent
    for json_file in sorted(locale_dir.glob("*.json")):
        locale_id = json_file.stem   # e.g. "en", "fr"
        _store.load_file(json_file, locale=locale_id)
    _store.set_locale("en")


def set_locale(locale: str) -> None:
    """Switch the active locale. Call after load_locales()."""
    _store.set_locale(locale)


def t(key: str, count: int | None = None, **kwargs) -> str:
    """Translate a key. Shorthand for _store.t(key, count=count, **kwargs)."""
    return _store.t(key, count=count, **kwargs)


def available_locales() -> list[str]:
    return _store.available_locales
