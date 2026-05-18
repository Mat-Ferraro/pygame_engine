"""
The engine renders strings it's given. LocaleStore determines which
strings get passed. It is a thin lookup layer that sits between your
game's string keys and the UI widgets that display them.

Locale file format (JSON)
-------------------------
A locale file is a flat or nested JSON object::

    {
        "menu.start":    "Start Game",
        "menu.quit":     "Quit",
        "hud.score":     "Score: {value}",
        "item.apple": {
            "one":   "1 apple",
            "other": "{count} apples"
        }
    }

Pluralisation
-------------
If the value for a key is a dict, it is treated as a plural form map.
Supported keys: ``"zero"``, ``"one"``, ``"other"`` (English-style).
Pass ``count=n`` to ``t()`` to select the right form::

    t("item.apple", count=1)   # → "1 apple"
    t("item.apple", count=5)   # → "5 apples"

Format substitution
-------------------
All values are passed through ``str.format_map(kwargs)`` so you can
embed dynamic values::

    t("hud.score", value=1234)   # → "Score: 1234"

Usage::

    from pygame_engine.locale import LocaleStore

    store = LocaleStore()
    store.load_file(Path("game/locale/en.json"), locale="en")
    store.load_file(Path("game/locale/fr.json"), locale="fr")
    store.set_locale("en")

    label.text = t("menu.start")         # "Start Game"
    label.text = t("hud.score", value=42)  # "Score: 42"
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocaleStore:
    """
    Manages locale files and resolves string keys to translated strings.

    Args:
        fallback_locale: Locale to fall back to when a key is missing from
                         the active locale. Default ``"en"``.
    """

    def __init__(self, fallback_locale: str = "en") -> None:
        self._locales:         dict[str, dict[str, Any]] = {}
        self._active:          str = fallback_locale
        self._fallback:        str = fallback_locale

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_file(self, path: Path, locale: str) -> None:
        """
        Load a JSON locale file and register it under ``locale``.

        Merges with any previously loaded keys for the same locale.

        Args:
            path:   Path to the ``.json`` locale file.
            locale: Locale identifier (e.g. ``"en"``, ``"fr"``, ``"ja"``).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid JSON.
        """
        if not path.exists():
            raise FileNotFoundError(f"Locale file not found: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in locale file {path}: {e}") from e

        if locale not in self._locales:
            self._locales[locale] = {}
        self._locales[locale].update(self._flatten(data))

    def load_dict(self, data: dict, locale: str) -> None:
        """
        Load a Python dict as a locale (useful in tests and tooling).

        Args:
            data:   Flat or nested string dict.
            locale: Locale identifier.
        """
        if locale not in self._locales:
            self._locales[locale] = {}
        self._locales[locale].update(self._flatten(data))

    # ── Locale switching ──────────────────────────────────────────────────────

    def set_locale(self, locale: str) -> None:
        """
        Switch the active locale.

        Args:
            locale: Locale identifier to activate.

        Raises:
            KeyError: If the locale has not been loaded.
        """
        if locale not in self._locales:
            raise KeyError(
                f"Locale {locale!r} not loaded. "
                f"Available: {sorted(self._locales.keys())}"
            )
        self._active = locale

    @property
    def active_locale(self) -> str:
        """The currently active locale identifier."""
        return self._active

    @property
    def available_locales(self) -> list[str]:
        """Sorted list of all loaded locale identifiers."""
        return sorted(self._locales.keys())

    def has_locale(self, locale: str) -> bool:
        """Return True if translations for the given locale code are loaded."""
        return locale in self._locales

    # ── Translation ───────────────────────────────────────────────────────────

    def t(
        self,
        key:     str,
        count:   int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Translate a key to a string in the active locale.

        Looks up ``key`` in the active locale, falls back to the fallback
        locale, then falls back to the key itself if not found anywhere.

        Args:
            key:    The string key to look up.
            count:  If provided, selects the appropriate plural form.
            **kwargs: Format substitution values applied to the result.

        Returns:
            The translated (and formatted) string.
        """
        value = self._lookup(key)

        # Plural form selection
        if isinstance(value, dict):
            value = self._select_plural(value, count)

        # Format substitution
        if kwargs or count is not None:
            fmt = dict(kwargs)
            if count is not None:
                fmt.setdefault("count", count)
            try:
                value = value.format_map(fmt)
            except (KeyError, IndexError):
                pass   # return the unformatted string rather than crashing

        return value

    def has_key(self, key: str) -> bool:
        """Return True if ``key`` exists in the active or fallback locale."""
        active = self._locales.get(self._active, {})
        if key in active:
            return True
        fallback = self._locales.get(self._fallback, {})
        return key in fallback

    # ── Internal ──────────────────────────────────────────────────────────────

    def _lookup(self, key: str) -> Any:
        """Return the raw value for key, falling back gracefully."""
        active = self._locales.get(self._active, {})
        if key in active:
            return active[key]
        fallback = self._locales.get(self._fallback, {})
        if key in fallback:
            return fallback[key]
        return key   # return key itself as last resort

    def _select_plural(self, forms: dict, count: int | None) -> str:
        """Select the right plural form for count."""
        if count is None:
            return forms.get("other", forms.get("one", next(iter(forms.values()))))
        if count == 0 and "zero" in forms:
            return forms["zero"]
        if count == 1 and "one" in forms:
            return forms["one"]
        return forms.get("other", forms.get("one", str(count)))

    def _flatten(self, data: dict, prefix: str = "") -> dict[str, Any]:
        """
        Flatten a nested dict to dot-separated keys.

        ``{"menu": {"start": "Go"}}`` → ``{"menu.start": "Go"}``

        Leaf values that are dicts with plural-form keys are kept as-is.
        """
        result: dict[str, Any] = {}
        plural_keys = {"zero", "one", "other"}
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict) and not set(v.keys()).issubset(plural_keys | set()):
                # Check if it's a plural form dict or a nested namespace
                if set(v.keys()) & plural_keys:
                    result[full_key] = v   # plural form dict — keep as-is
                else:
                    result.update(self._flatten(v, full_key))
            else:
                result[full_key] = v
        return result

    def __repr__(self) -> str:
        return (f"LocaleStore(active={self._active!r}, "
                f"locales={self.available_locales})")