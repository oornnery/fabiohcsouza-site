"""blog.fabiohcsouza.dev: its pages. The newsletter's own routes are in app.api.routes.newsletter."""

from fastapi import Depends, HTTPException, Request

from ...content import Content
from ...core.i18n import N_
from ..deps import maintenance, render_page
from ..pages import Pages
from .newsletter import newsletter_on

router = Pages("blog", dependencies=[Depends(maintenance)])


def subscribe_page(request: Request, sent: bool = False):
    newsletter_on(request.app.state.settings)
    return render_page(request, "blog/newsletter.html", state="sent" if sent else "form")


def _post(c: Content, slug: str) -> dict:
    if (post := c.blog.by_slug.get(slug)) is None:
        raise HTTPException(404)
    return {"post": post, **c.blog.neighbors(post)}


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
router.add("/posts/{slug}", "blog/post.html", nav="/posts", context=_post,
           each=lambda c: [{"slug": p.slug} for p in [*c.blog.posts, *c.blog.project_posts]],
           lastmod=lambda c, slug: c.blog.by_slug[slug].updated, langs=lambda c, slug: list(c.blog.by_slug[slug].versions))
router.add("/subscribe", "blog/newsletter.html", endpoint=subscribe_page, menu=N_("Newsletter"), header=False,
           flag="newsletter")
