"""EN (default) and PT-BR with gettext (Babel).

Interface strings are written in English where they are used and marked for translation:
    templates   {{ _("Posts") }}, {% trans n=… %}…{% endtrans %}   (jinja2.ext.i18n, new style: %(name)s, autoescaped)
    Python      i18n.t("Field notes", lang), N_("Works") for strings translated later (menus, messages)
    JavaScript  FS.t("Sending…")   (the PT strings reach the browser in <meta name="fs:strings">)

Catalog: app/locales/pt_BR/LC_MESSAGES/messages.po, read at start (no .mo to build or commit). After changing strings:
`python -m app i18n` extracts them and updates the .po; a test fails while any string has no translation.
Dates and month names come from Babel too (app.utils.web.Page.date/month).

URLs: English at /, Portuguese under /pt/ (app.core.security.Guard strips the prefix and sets the language)."""

import json
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache
from gettext import NullTranslations
from io import BytesIO
from typing import Any, cast

from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from babel.support import Translations
from jinja2 import Environment

from .config import APP

LANGS = ("en", "pt")  # the first is the default (served at /, the language of the source strings), the others under /<lang>/
SOURCE = "pt"  # content is written in Portuguese; <slug>.en.md is the translation
HTML_LANG = {"en": "en", "pt": "pt-BR"}
OG_LOCALE = {"en": "en_US", "pt": "pt_BR"}
LOCALES = APP / "locales"
LANG: ContextVar[str] = ContextVar("lang", default=LANGS[0])  # the language being rendered (see use())


def prefix(lang: str) -> str:
    """URL prefix of a language: '' for English, '/pt' for Portuguese."""
    return "" if lang == LANGS[0] else f"/{lang}"


def locale(lang: str) -> str:
    return OG_LOCALE[lang]  # pt -> pt_BR (the catalog folder and Babel's locale)


def po_path(lang: str):  # noqa: ANN201
    return LOCALES / locale(lang) / "LC_MESSAGES" / "messages.po"


@cache
def catalog(lang: str) -> Catalog:
    with po_path(lang).open("rb") as f:
        return read_po(f, locale=locale(lang))


@cache
def translations(lang: str) -> NullTranslations:
    if lang == LANGS[0]:
        return NullTranslations()
    buf = BytesIO()
    write_mo(buf, catalog(lang))  # fuzzy entries are left out, as with a compiled .mo
    buf.seek(0)
    return Translations(buf)


def t(text: str, lang: str) -> str:
    return translations(lang).gettext(text)


def N_(text: str) -> str:  # noqa: N802 — gettext convention
    """Marks a string for extraction; it is translated where it is shown (menus, messages)."""
    return text


def gettext(text: str) -> str:
    return translations(LANG.get()).gettext(text)


def ngettext(singular: str, plural: str, n: int) -> str:
    return translations(LANG.get()).ngettext(singular, plural, n)


@contextmanager
def use(lang: str) -> Generator[None]:
    """Renders inside this block use `lang` (templates, macros and e-mails read it from LANG)."""
    token = LANG.set(lang)
    try:
        yield
    finally:
        LANG.reset(token)


def install(env: Environment) -> None:
    env.add_extension("jinja2.ext.i18n")
    # the extension adds install_gettext_callables() to the environment at runtime (not in its type)
    cast("Any", env).install_gettext_callables(gettext, ngettext, newstyle=True)


def js_dict(lang: str) -> str:
    """The strings marked in static/assets/js ({english: translation}) for <meta name="fs:strings">."""
    if lang == LANGS[0]:
        return "{}"
    found = {m.id: m.string for m in catalog(lang) if m.id and m.string and not m.fuzzy
             and any(path.endswith(".js") for path, _ in m.locations)}
    return json.dumps(found, ensure_ascii=False, separators=(",", ":"))
