"""robots.txt, sitemap.xml (with hreflang alternates), security.txt, the share image (og.png), the icons and /media
(the images in each content folder's assets/): the same routes on every site. The blog adds rss.xml (`feed`)."""

import re
from datetime import UTC, datetime, time, timedelta
from email.utils import format_datetime
from html import escape  # writing XML only: & < > " ' escaped

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response

from ...content import Content
from ...core import i18n
from ...core.config import STATIC, Settings
from ...utils import markdown
from ..deps import ContentDep, SettingsDep
from ..pages import Pages

router = APIRouter()
feed = APIRouter()  # the blog only

DAY = {"Cache-Control": "public, max-age=86400"}  # fixed URLs (no ?v=): crawlers and browsers ask for them by name


def security_txt(settings: Settings, site: str, email: str) -> str:
    """RFC 9116. Expires must be under a year away: computed on each request."""
    expires = (datetime.now(UTC) + timedelta(days=180)).strftime("%Y-%m-%dT00:00:00Z")
    return (f"Contact: mailto:{email}\nExpires: {expires}\nPreferred-Languages: en, pt\n"
            f"Canonical: {settings.site_url(site)}/.well-known/security.txt\n")


def robots(settings: Settings, site: str) -> str:
    return f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {settings.site_url(site)}/sitemap.xml\n"


def sitemap(settings: Settings, pages: Pages, c: Content, langs: tuple[str, ...] = i18n.LANGS) -> str:
    base = settings.site_url(pages.site)
    rows = []
    for page, path, params in pages.urls(c):
        if not page.sitemap:
            continue
        have = [lang for lang in langs if not page.langs or lang in page.langs(c, **params)]  # a post's own languages
        day = page.lastmod(c, **params) if page.lastmod else None
        mod = f"<lastmod>{day.isoformat()}</lastmod>" if day else ""
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{i18n.HTML_LANG[a]}" href="{escape(base + i18n.prefix(a) + path)}"/>'
                       for a in have if len(have) > 1)
        rows.extend(f"<url><loc>{escape(base + i18n.prefix(lang) + path)}</loc>{mod}{alts}</url>" for lang in have)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n"
    )


def _site(request: Request) -> str:
    return request.app.state.site


@router.get("/robots.txt")
def robots_txt(request: Request, settings: SettingsDep):
    return PlainTextResponse(robots(settings, _site(request)))


@router.get("/.well-known/security.txt")
def security_txt_route(request: Request, settings: SettingsDep, c: ContentDep):
    return PlainTextResponse(security_txt(settings, _site(request), c.site["email"]))


@router.get("/sitemap.xml")
def sitemap_xml(request: Request, settings: SettingsDep, c: ContentDep):
    return Response(sitemap(settings, request.app.state.pages, c), media_type="application/xml")


@router.get("/og.png")
def og(request: Request):
    return FileResponse(STATIC / "assets" / "img" / f"og-{_site(request)}.png", media_type="image/png", headers=DAY)


@router.get("/favicon.ico")
def favicon():
    return FileResponse(STATIC / "assets" / "img" / "favicon.svg", media_type="image/svg+xml", headers=DAY)


@router.get("/apple-touch-icon.png")
def touch_icon():  # iOS asks for this path when the site goes to the home screen (it ignores SVG icons)
    return FileResponse(STATIC / "assets" / "img" / "touch-icon.png", media_type="image/png", headers=DAY)


NAME = re.compile(r"^[\w-][\w.-]*$")
MEDIA = ("pages", "posts", "projects")


@router.get("/media/{kind}/{slug}/{name}")
def media(kind: str, slug: str, name: str, settings: SettingsDep, c: ContentDep):
    """An image of a page, post or project: content/<kind>/<slug>/assets/<name>. Images only, nothing outside that
    folder, and nothing of a draft post in production."""
    if kind not in MEDIA or not (NAME.match(slug) and NAME.match(name)) or (kind == "posts" and slug not in c.blog.by_slug):
        raise HTTPException(404)
    folder = (settings.content_dir / kind / slug / "assets").resolve()
    file = (folder / name).resolve()
    if not (file.is_relative_to(folder) and file.suffix.lower() in markdown.IMAGES and file.is_file()):
        raise HTTPException(404)
    return FileResponse(file, headers=DAY)


def rss(settings: Settings, c: Content, lang: str = "en", limit: int = 30) -> str:
    posts = c.blog.posts
    base = settings.blog_url + i18n.prefix(lang)
    items = []
    for p in posts[:limit]:
        v = p.v(lang)
        url = f"{settings.blog_url}{i18n.prefix(lang if p.translated(lang) else p.source)}/posts/{p.slug}"
        date = format_datetime(datetime.combine(p.created, time(12), UTC))
        cats = "".join(f"<category>{escape(t)}</category>" for t in p.tags)
        items.append(
            f"<item><title>{escape(v.title)}</title><link>{escape(url)}</link>"
            f'<guid isPermaLink="true">{escape(url)}</guid><pubDate>{date}</pubDate>'
            f"<description>{escape(v.summary)}</description>"
            f"<content:encoded>{escape(v.html)}</content:encoded>{cats}</item>"  # the whole post: readers stay in the feed
        )
    title = f"{i18n.t('Field notes', lang)} · {c.site['name']}"
    newest = max((p.updated for p in posts), default=None)
    built = f"<lastBuildDate>{format_datetime(datetime.combine(newest, time(12), UTC))}</lastBuildDate>" if newest else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>'
        f"<title>{escape(title)}</title><link>{escape(base)}/</link>"
        f"<description>{escape(i18n.t('Notes on VoIP, networks, automation, code and AI.', lang))}</description>"
        f"<language>{i18n.HTML_LANG[lang].lower()}</language>{built}"
        f'<atom:link href="{escape(base)}/rss.xml" rel="self" type="application/rss+xml"/>' + "".join(items) + "</channel></rss>\n"
    )



@feed.get("/rss.xml")
def rss_xml(request: Request, settings: SettingsDep, c: ContentDep):
    return Response(rss(settings, c, request.state.lang), media_type="application/xml")  # browsers download rss+xml; this opens in a tab
