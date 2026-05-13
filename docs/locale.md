## Purpose

String key → translated string lookup. The engine renders strings it's
given — localisation determines which strings get passed. Pure Python,
no pygame dependency.

---

## Quick start

```python
from pathlib import Path
from pygame_engine.locale import LocaleStore

store = LocaleStore(fallback_locale="en")
store.load_file(Path("game/locale/en.json"), locale="en")
store.load_file(Path("game/locale/fr.json"), locale="fr")
store.set_locale("en")

label.text = store.t("menu.start")           # "Start Game"
label.text = store.t("hud.score", value=42)  # "Score: 42"
label.text = store.t("item.apple", count=3)  # "3 apples"
```

---

## JSON format

```json
{
    "menu.start":  "Start Game",
    "hud.score":   "Score: {value}",
    "item.apple": {
        "one":   "1 apple",
        "other": "{count} apples"
    }
}
```

Nested dicts flatten to dot keys: `{"menu": {"start": "Go"}}` → `"menu.start"`.

---

## API

```python
store.load_file(path, locale="en")
store.load_dict(data, locale="en")
store.set_locale("fr")
store.active_locale          # current locale id
store.available_locales      # sorted list
store.has_locale("fr")
store.has_key("menu.start")  # checks active + fallback

store.t("key")
store.t("hud.score", value=42)
store.t("item.apple", count=1)   # "1 apple"
store.t("item.apple", count=5)   # "5 apples"
```

Missing keys return the key itself. Missing format args leave the
template unchanged. Neither crashes.

---

## Game template integration

```python
from game.locale import t, load_locales, set_locale

load_locales()               # once at startup
label.text = t("menu.start")
set_locale("fr")             # hot-swap
```

## Plural forms

Supported: `"zero"`, `"one"`, `"other"`.

```json
"item.life": {"zero": "No lives", "one": "1 life", "other": "{count} lives"}
```