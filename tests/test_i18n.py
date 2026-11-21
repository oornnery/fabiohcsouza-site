"""The translation catalog (app/locales) stays complete and in sync with the code."""

import re

import pytest
from babel.messages.extract import extract_from_dir
from babel.messages.frontend import parse_mapping_cfg

from app.core import i18n
from app.core.config import ROOT

PLACEHOLDER = re.compile(r"%\((\w+)\)s")
TAG = re.compile(r"<[^>]+>")


def _extracted() -> set[str]:
    with (ROOT / "babel.cfg").open() as f:
        method_map, options_map = parse_mapping_cfg(f)
    keywords = {"_": None, "N_": None, "t": None, "gettext": None, "ngettext": (1, 2), "FS.t": None}
    found = set()
    for _, _, message, _, _ in extract_from_dir(ROOT, method_map, options_map, keywords=keywords):
        found.update([message] if isinstance(message, str) else [m for m in message if m])
    return found


@pytest.mark.parametrize("lang", i18n.LANGS[1:])
def test_catalog_is_up_to_date_and_complete(lang):
    catalog = i18n.catalog(lang)
    ids = {m.id for m in catalog if m.id}
    code = _extracted()
    assert not code - ids, f"new strings, run `python -m app i18n`: {sorted(code - ids)[:5]}"
    assert not ids - code, f"strings no longer used, run `python -m app i18n`: {sorted(ids - code)[:5]}"
    assert not [m.id for m in catalog if m.id and (not m.string or m.fuzzy)], "untranslated or fuzzy entries in the .po"


@pytest.mark.parametrize("lang", i18n.LANGS[1:])
def test_translations_keep_placeholders_and_markup(lang):
    """A translation can't drop a %(link)s, add HTML or change a link: the markup in msgid is the only markup."""
    for m in i18n.catalog(lang):
        if isinstance(m.id, str) and m.id and isinstance(m.string, str) and m.string:
            assert sorted(PLACEHOLDER.findall(m.id)) == sorted(PLACEHOLDER.findall(m.string)), m.id
            assert TAG.findall(m.id) == TAG.findall(m.string), m.id


def test_js_strings_reach_the_browser():
    assert "Sending…" in i18n.js_dict("pt") and "Enviando…" in i18n.js_dict("pt") and i18n.js_dict("en") == "{}"
    assert "Posts" not in i18n.js_dict("pt")  # only the strings the scripts use
