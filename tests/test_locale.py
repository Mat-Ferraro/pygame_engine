"""
tests/test_locale.py — LocaleStore tests.
"""

import json
import tempfile
from pathlib import Path

import pytest

from pygame_engine.locale import LocaleStore


EN = {
    "menu.start":  "Start Game",
    "menu.quit":   "Quit",
    "hud.score":   "Score: {value}",
    "item.apple": {"one": "1 apple", "other": "{count} apples"},
    "item.life":  {"zero": "No lives", "one": "1 life", "other": "{count} lives"},
}

FR = {
    "menu.start": "Commencer",
    "menu.quit":  "Quitter",
}


# ── Loading ───────────────────────────────────────────────────────────────────

def test_load_dict() -> None:
    store = LocaleStore()
    store.load_dict(EN, locale="en")
    assert store.has_locale("en")


def test_load_file(tmp_path) -> None:
    p = tmp_path / "en.json"
    p.write_text(json.dumps(EN), encoding="utf-8")
    store = LocaleStore()
    store.load_file(p, locale="en")
    assert store.has_locale("en")


def test_load_file_missing_raises(tmp_path) -> None:
    store = LocaleStore()
    with pytest.raises(FileNotFoundError):
        store.load_file(tmp_path / "nope.json", locale="en")


def test_load_file_invalid_json_raises(tmp_path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    store = LocaleStore()
    with pytest.raises(ValueError, match="Invalid JSON"):
        store.load_file(p, locale="en")


def test_load_merges_existing() -> None:
    store = LocaleStore()
    store.load_dict({"a": "A"}, locale="en")
    store.load_dict({"b": "B"}, locale="en")
    store.set_locale("en")
    assert store.t("a") == "A"
    assert store.t("b") == "B"


def test_nested_dict_flattened() -> None:
    store = LocaleStore()
    store.load_dict({"menu": {"start": "Go", "quit": "Exit"}}, locale="en")
    store.set_locale("en")
    assert store.t("menu.start") == "Go"
    assert store.t("menu.quit")  == "Exit"


# ── Locale switching ──────────────────────────────────────────────────────────

def test_set_locale_switches_active() -> None:
    store = LocaleStore()
    store.load_dict(EN, locale="en")
    store.load_dict(FR, locale="fr")
    store.set_locale("fr")
    assert store.active_locale == "fr"


def test_set_locale_unknown_raises() -> None:
    store = LocaleStore()
    with pytest.raises(KeyError):
        store.set_locale("zz")


def test_available_locales_sorted() -> None:
    store = LocaleStore()
    store.load_dict(EN, locale="en")
    store.load_dict(FR, locale="fr")
    assert store.available_locales == ["en", "fr"]


# ── Translation ───────────────────────────────────────────────────────────────

def make_store() -> LocaleStore:
    store = LocaleStore(fallback_locale="en")
    store.load_dict(EN, locale="en")
    store.load_dict(FR, locale="fr")
    store.set_locale("en")
    return store


def test_t_simple_lookup() -> None:
    assert make_store().t("menu.start") == "Start Game"


def test_t_missing_key_returns_key() -> None:
    assert make_store().t("unknown.key") == "unknown.key"


def test_t_falls_back_to_fallback_locale() -> None:
    store = make_store()
    store.set_locale("fr")
    # "hud.score" not in FR, should fall back to EN
    assert store.t("hud.score", value=99) == "Score: 99"


def test_t_active_locale_preferred_over_fallback() -> None:
    store = make_store()
    store.set_locale("fr")
    assert store.t("menu.start") == "Commencer"


def test_t_format_substitution() -> None:
    assert make_store().t("hud.score", value=42) == "Score: 42"


def test_t_format_missing_kwarg_returns_template() -> None:
    # Missing substitution key should not crash
    result = make_store().t("hud.score")   # missing value=
    assert "Score" in result   # returns template or partial


def test_t_plural_one() -> None:
    assert make_store().t("item.apple", count=1) == "1 apple"


def test_t_plural_other() -> None:
    assert make_store().t("item.apple", count=5) == "5 apples"


def test_t_plural_zero_form() -> None:
    assert make_store().t("item.life", count=0) == "No lives"


def test_t_plural_one_form_life() -> None:
    assert make_store().t("item.life", count=1) == "1 life"


def test_t_plural_other_form_life() -> None:
    assert make_store().t("item.life", count=3) == "3 lives"


def test_t_plural_without_count_uses_other() -> None:
    result = make_store().t("item.apple")
    assert "apple" in result


def test_t_count_injected_as_kwarg() -> None:
    store = make_store()
    result = store.t("item.apple", count=7)
    assert result == "7 apples"


def test_has_key_true_for_known() -> None:
    assert make_store().has_key("menu.start") is True


def test_has_key_false_for_unknown() -> None:
    assert make_store().has_key("does.not.exist") is False


def test_has_key_checks_fallback() -> None:
    store = make_store()
    store.set_locale("fr")
    # "hud.score" only in EN (fallback)
    assert store.has_key("hud.score") is True


# ── Hot-swap locale ───────────────────────────────────────────────────────────

def test_hot_swap_locale() -> None:
    store = make_store()
    assert store.t("menu.start") == "Start Game"
    store.set_locale("fr")
    assert store.t("menu.start") == "Commencer"
    store.set_locale("en")
    assert store.t("menu.start") == "Start Game"


# ── repr ──────────────────────────────────────────────────────────────────────

def test_repr() -> None:
    store = make_store()
    r = repr(store)
    assert "LocaleStore" in r
    assert "en" in r
