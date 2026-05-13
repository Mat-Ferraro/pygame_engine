# Localisation

## Purpose

String key → translated string lookup. The engine renders strings it's
given — localisation determines which strings get passed.

`LocaleStore` is a pure lookup layer with no pygame dependency.

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

## Locale file format (JSON)

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

Nested dicts are flattened to dot-separated keys:
`{"menu": {"start": "Go"}}` → `"menu.start"`.

---

## LocaleStore API

```python
store.load_file(path, locale="en")      # load from .json file
store.load_dict(data, locale="en")      # load from Python dict
store.set_locale("fr")                  # switch active locale
store.active_locale                     # current locale id
store.available_locales                 # sorted list of loaded locales
store.has_locale("fr")                  # bool
store.has_key("menu.start")             # bool — checks active + fallback

store.t("menu.start")                   # simple lookup
store.t("hud.score", value=42)          # format substitution
store.t("item.apple", count=1)          # plural: "1 apple"
store.t("item.apple", count=5)          # plural: "5 apples"
```

Missing keys return the key itself. Missing format args leave the
template unchanged. Both fail gracefully rather than crashing.

---

## Plural forms

Supported keys: `"zero"`, `"one"`, `"other"`.

```json
"item.life": {
    "zero":  "No lives",
    "one":   "1 life",
    "other": "{count} lives"
}
```

```python
store.t("item.life", count=0)   # "No lives"
store.t("item.life", count=1)   # "1 life"
store.t("item.life", count=3)   # "3 lives"
```

---

## Game template integration

The game template ships with `game/locale/` containing:
- `en.json` — default English strings
- `__init__.py` — exposes `t()`, `load_locales()`, `set_locale()`

```python
from game.locale import t, load_locales, set_locale

# In main.py startup:
load_locales()

# Anywhere in game code:
label.text = t("menu.start")

# Settings screen:
set_locale("fr")
```

## Hot-swap locale

`set_locale()` switches immediately. Widgets that hold string references
need to refresh — call `t()` again in their next `update()` cycle or
subscribe to a `"locale.changed"` bus event if you fire one from your
settings code.
