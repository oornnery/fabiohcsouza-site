"""fabiohcsouza.dev: its pages. Each `router.add` is a route, a sitemap entry and, with `menu`, a menu link."""

from fastapi import Depends, HTTPException, Request

from ...content import Content
from ...core.i18n import N_
from ..deps import maintenance, render_page
from ..pages import Pages

router = Pages("portfolio", dependencies=[Depends(maintenance)])


def _project(c: Content, slug: str) -> dict:
    if (project := c.project_page(slug)) is None:
        raise HTTPException(404)
    return {"project": project}


def contact_page(request: Request, sent: bool = False):
    return render_page(request, "portfolio/contact.html", sent=sent)


router.add("/", "portfolio/home.html", menu=N_("Home"))
router.add("/projects", "portfolio/projects.html", menu=N_("Projects"))
router.add("/projects/{slug}", "portfolio/project.html", nav="/projects", context=_project,
           each=lambda c: [{"slug": p.slug} for p in c.project_pages],
           lastmod=lambda c, slug: c.project_page(slug).updated)
router.link(N_("Blog"), "/", site="blog", footer=False)  # shown only with BLOG=true (Page.shows)
router.add("/about", "portfolio/about.html", menu=N_("About"))
router.add("/privacy", "portfolio/privacy.html", menu=N_("Privacy"), header=False)
router.add("/contact", "portfolio/contact.html", endpoint=contact_page, menu=N_("Contact"))
