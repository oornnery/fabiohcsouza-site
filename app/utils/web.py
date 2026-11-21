"""Page rendering: the Jinja environment and Page, everything a template needs for links, assets, text and dates.

URLs are paths on the same site (/projects, /pt/projects) and the other site's origin for cross-site links; assets are
versioned (/assets/css/base.css?v=<hash>) so they can be cached forever."""

import datetime as dt
import hashlib
import json
from collections.abc import MutableMapping
from dataclasses import dataclass
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path
from typing import Any, cast

from babel.dates import format_date, format_skeleton
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

from ..content import Content
from ..core import i18n
from ..core.config import APP, DOMAINS, STATIC, Settings
from . import schema

TEMPLATES = APP / "templates"


@lru_cache(maxsize=256)
def _hash(path: Path, mtime: float) -> str:  # mtime in the key: a changed file gets a new hash
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


@lru_cache(maxsize=256)
def _asset(name: str) -> str:
    f = STATIC / "assets" / name
    return f"/assets/{name}?v={_hash(f, f.stat().st_mtime) if f.exists() else '0'}"


@dataclass
class Page:
    """Everything a template needs to build links for the current page."""

    settings: Settings
    site: str
    lang: str = "en"
    path: str = "/"  # canonical path of this page, without the /pt prefix
    status: int = 200
    nav: str = ""  # nav item marked current (default: path); a post marks /posts

    def __post_init__(self):
        self.nav = self.nav or self.path

    # ---- links
    def url(self, path: str = "/", site: str | None = None, lang: str | None = None, absolute: bool = False) -> str:
        site, lang = site or self.site, lang or self.lang
        frag = ""
        if "#" in path:
            path, frag = path.split("#", 1)
            frag = "#" + frag
        query = ""
        if "?" in path:
            path, query = path.split("?", 1)
            query = "?" + query
        prefix = i18n.prefix(lang)
        # one leading slash: a request for //evil.example must not turn into a link to another site (404 page)
        full = prefix + "/" + path.lstrip("/")
        if site != self.site or absolute:
            return self.settings.site_url(site) + full + query + frag
        return full + query + frag

    def shows(self, site: str) -> bool:
        """Whether this page links to `site`: always, except the blog from the portfolio while BLOG is off."""
        return site != "blog" or self.site == "blog" or self.settings.blog

    def langs(self, have: list[str] | None = None) -> list[str]:
        """The languages this page exists in, the site's order (`have`: a post's versions; default: all)."""
        return [lang for lang in i18n.LANGS if have is None or lang in have]

    def canonical(self, have: list[str] | None = None) -> str:
        """This page's own URL. A post without a version in this language is the same text at two URLs: the
        canonical one is the language it was written in."""
        langs = self.langs(have)
        return self.url(self.path, lang=self.lang if self.lang in langs else langs[0], absolute=True)

    def og_image(self, image: str | None = None) -> str:
        """The share image: a post's own (its URL path, /media/…) or the site's og.png."""
        return self.settings.site_url(self.site) + (image or "/og.png")

    def asset(self, name: str) -> str:
        return _asset(name) if self.settings.production else _asset.__wrapped__(name)  # production: files never change

    # ---- text
    def t(self, text: str) -> str:
        return i18n.t(text, self.lang)

    def date(self, d: dt.date, year: bool = True) -> str:
        """Babel/CLDR: 'Sep 8, 2026' / '8 de set. de 2026' (without year: 'Sep 8' / '8 de set.')."""
        return format_skeleton("yMMMd" if year else "MMMd", d, locale=self.locale)

    def month(self, n: int, full: bool = False) -> str:
        """A month as a label: 'Sep' / 'Set', 'September' / 'Setembro' (CLDR writes PT months lowercase, with a dot)."""
        return format_date(dt.date(2000, n, 1), "LLLL" if full else "LLL", locale=self.locale).rstrip(".").capitalize()

    @property
    def domain(self) -> str:
        """The site's public name ('fabiohcsouza.dev'), the same in development."""
        return DOMAINS[self.site]

    @property
    def locale(self) -> str:
        return i18n.HTML_LANG[self.lang].replace("-", "_")

    @property
    def html_lang(self) -> str:
        return i18n.HTML_LANG[self.lang]

    @property
    def og_locale(self) -> str:
        return i18n.OG_LOCALE[self.lang]

    @property
    def status_phrase(self) -> str:
        """'not found', 'too many requests'… from the standard library (no list of our own)."""
        try:
            return HTTPStatus(self.status).phrase.lower()
        except ValueError:
            return "error"

    @property
    def js_strings(self) -> str:
        return i18n.js_dict(self.lang)


def _json_ld(data: dict) -> Markup:
    # </script> can't appear: "<" is escaped, so the JSON is safe inside a <script type="application/ld+json">
    return Markup(json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c"))  # noqa: S704 — "<" is escaped  # nosec B704


class Macros:
    """`ui.<name>(...)` in any template: the macro <name> from templates/ui/<name>.html (one macro per file).
    Global, so no template imports anything; looked up on use, so edits reload like any template."""

    def __init__(self, env: Environment):
        self._env = env

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._env.get_template(f"ui/{name}.html").module, name)


def template_globals(env: Environment) -> MutableMapping[str, Any]:
    """Environment.globals holds any value; Jinja only types it from its defaults."""
    return cast("MutableMapping[str, Any]", env.globals)


def _environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html", "xml", "txt"]),
        undefined=StrictUndefined,  # a typo in a template fails loudly instead of rendering empty
        trim_blocks=True,
        lstrip_blocks=True,
        auto_reload=False,  # app.main turns it on in development (production templates never change)
    )
    i18n.install(env)  # _() and {% trans %}
    env.filters["json_ld"] = _json_ld
    template_globals(env).update(now=lambda: dt.datetime.now(dt.UTC), ui=Macros(env))
    return env


templates = _environment()
template_globals(templates).update(schema=schema, html_langs=i18n.HTML_LANG)


def render(template: str, p: Page, content: Content, **context) -> str:
    """A page as HTML. Context: p (this Page), c (the content), me (content/site.yml) + the page's own values."""
    with i18n.use(p.lang):
        return templates.get_template(template).render(p=p, c=content, me=content.site, **context)
