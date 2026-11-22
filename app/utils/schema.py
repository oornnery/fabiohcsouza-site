"""Structured data (schema.org JSON-LD): the person, the portfolio and the blog. Templates call
`schema.<page>(p, c, …)`; base.html writes the result with the json_ld filter.
Built here, not in Jinja: plain dicts, testable, one place per type."""

from typing import TYPE_CHECKING

from ..content import Content
from ..core import i18n

if TYPE_CHECKING:
    from ..content.posts import Post
    from ..content.projects import Project
    from .web import Page  # app.utils.web imports this module (the `schema` template global)

CONTEXT = "https://schema.org"


def _me(p: Page) -> str:
    return p.settings.portfolio_url + "/#me"


def author(p: Page, c: Content) -> dict:
    return {"@type": "Person", "@id": _me(p), "name": c.site["name"], "url": p.settings.portfolio_url}


def portfolio_home(p: Page, c: Content) -> dict:
    me, url = c.site, p.settings.portfolio_url
    person = {
        **author(p, c), "image": f"{url}/assets/{me['avatar']}", "email": f"mailto:{me['email']}", "jobTitle": me["role"][p.lang],
        "worksFor": {"@type": "Organization", "name": me["company"]},
        "address": {"@type": "PostalAddress", "addressLocality": me["city"], "addressCountry": me["country"]},
        "knowsAbout": me["knows_about"], "sameAs": [me["socials"]["github"], me["socials"]["linkedin"]],
    }
    site = {"@type": "WebSite", "@id": f"{url}/#site", "url": url, "name": p.domain, "inLanguage": list(i18n.HTML_LANG.values()),
            "publisher": {"@id": _me(p)}}
    return {"@context": CONTEXT, "@graph": [person, site]}


def about(p: Page, c: Content) -> dict:
    return {"@context": CONTEXT, "@type": "ProfilePage", "url": p.canonical(),
            "mainEntity": {"@type": "Person", "@id": _me(p), "name": c.site["name"]}}


def contact(p: Page, c: Content) -> dict:
    return {"@context": CONTEXT, "@type": "ContactPage", "url": p.canonical(),
            "mainEntity": {"@type": "Person", "@id": _me(p), "name": c.site["name"], "email": f"mailto:{c.site['email']}"}}


def projects(p: Page, c: Content, title: str) -> dict:
    return {"@context": CONTEXT, "@type": "CollectionPage", "name": title, "url": p.canonical(),
            "hasPart": [{"@type": "SoftwareSourceCode", "name": w.title(p.lang), "description": w.desc[p.lang],
                        **({"codeRepository": w.links["repo"]} if "repo" in w.links else {})} for w in c.open_source]}


def project(p: Page, c: Content, w: Project) -> dict:
    data = {"@context": CONTEXT, "@type": "SoftwareSourceCode" if "repo" in w.links else "CreativeWork",
            "name": w.title(p.lang), "description": w.desc[p.lang], "url": p.canonical(), "keywords": ", ".join(w.tags),
            "author": author(p, c)}
    if "repo" in w.links:
        data["codeRepository"] = w.links["repo"]
    if w.updated:
        data["dateModified"] = w.updated.isoformat()
    return data


# ---- the blog

def blog_home(p: Page, c: Content) -> dict:
    return {"@context": CONTEXT, "@type": "Blog", "@id": p.settings.blog_url + "/#blog", "name": p.t("Field notes"),
            "url": p.settings.blog_url, "inLanguage": p.html_lang, "author": author(p, c)}


def posts(p: Page, title: str) -> dict:
    return {"@context": CONTEXT, "@type": "CollectionPage", "name": title, "url": p.canonical(),
            "isPartOf": {"@id": p.settings.blog_url + "/#blog"}}


def post(p: Page, c: Content, post: Post) -> dict:
    v = post.v(p.lang)
    article = {
        "@type": "BlogPosting", "headline": v.title, "description": v.summary, "url": p.canonical(),
        "datePublished": post.created.isoformat(), "dateModified": post.updated.isoformat(),
        "inLanguage": p.html_lang if post.translated(p.lang) else i18n.HTML_LANG[post.source], "keywords": ", ".join(post.tags),
        "wordCount": v.words, "image": p.og_image(post.image), "mainEntityOfPage": p.canonical(),
        "isPartOf": {"@id": p.settings.blog_url + "/#blog"}, "author": author(p, c),
    }
    crumbs = [("Blog", p.url("/", absolute=True)), (p.t("Posts"), p.url("/posts", absolute=True)), (v.title, p.canonical())]
    breadcrumbs = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": name, "item": url} for i, (name, url) in enumerate(crumbs, 1)]}
    return {"@context": CONTEXT, "@graph": [article, breadcrumbs]}
