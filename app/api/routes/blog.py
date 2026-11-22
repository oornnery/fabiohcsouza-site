"""blog.fabiohcsouza.dev: its pages and the likes of a post. The newsletter's own routes are in
app.api.routes.newsletter.

    POST /api/posts/<slug>/like     one more like: JSON {"likes": n} for post.js, a redirect for a plain form POST.
                                    Only the total is kept; the browser remembers it liked (localStorage)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from ... import crud
from ...content import Content
from ...core import i18n, security
from ...core.i18n import N_
from ..deps import ContentDep, EngineDep, SettingsDep, maintenance, render_page
from ..pages import Pages
from .newsletter import newsletter_on

router = Pages("blog", dependencies=[Depends(maintenance)])
api = APIRouter(prefix="/api", dependencies=[Depends(maintenance)])
LIKE_LIMIT = 20  # likes per IP per FORM_WINDOW_SECONDS


def subscribe_page(request: Request, sent: bool = False):
    newsletter_on(request.app.state.settings)
    return render_page(request, "blog/newsletter.html", state="sent" if sent else "form")


def _post(c: Content, slug: str) -> dict:
    if (post := c.blog.by_slug.get(slug)) is None:
        raise HTTPException(404)
    return {"post": post, **c.blog.neighbors(post)}


def post_page(request: Request, slug: str, c: ContentDep, engine: EngineDep):
    with Session(engine) as s:
        likes = crud.likes(s, slug)
    return render_page(request, "blog/post.html", nav="/posts", likes=likes, **_post(c, slug))


@api.post("/posts/{slug}/like")
def like(request: Request, slug: str, c: ContentDep, settings: SettingsDep, engine: EngineDep):
    _post(c, slug)  # 404 for a post that doesn't exist (or is a draft in production)
    key = f"like:{security.client_key(request.state.client_ip)}"
    if not security.db_hit(engine, key, LIKE_LIMIT, settings.form_window_seconds):
        raise HTTPException(429, "too many requests")
    with Session(engine) as s:
        count = crud.like(s, slug)
    if "application/json" in request.headers.get("accept", ""):
        return {"likes": count}
    return RedirectResponse(f"{i18n.prefix(request.state.lang)}/posts/{slug}#like", 303)


def _tag(c: Content, tag: str) -> dict:
    if not (posts := [p for p in c.blog.posts if tag in p.tags]):
        raise HTTPException(404)
    return {"tag": tag, "posts": posts}


router.add("/", "blog/home.html", menu=N_("Home"))
router.add("/posts", "blog/posts.html", menu=N_("Posts"))
router.add("/tags", "blog/tags.html", menu=N_("Tags"))
router.add("/tags/{tag}", "blog/tags.html", nav="/tags", context=_tag, each=lambda c: [{"tag": t} for t, _ in c.blog.tags])
router.add("/timeline", "blog/timeline.html", menu=N_("Timeline"))
router.link(N_("Portfolio"), "/", site="portfolio", footer=False)
router.link("RSS", "/rss.xml", header=False)
router.add("/posts/{slug}", "blog/post.html", endpoint=post_page, nav="/posts", context=_post,
           each=lambda c: [{"slug": p.slug} for p in [*c.blog.posts, *c.blog.project_posts]],
           lastmod=lambda c, slug: c.blog.by_slug[slug].updated, langs=lambda c, slug: list(c.blog.by_slug[slug].versions))
router.add("/subscribe", "blog/newsletter.html", endpoint=subscribe_page, menu=N_("Newsletter"), header=False,
           flag="newsletter")
