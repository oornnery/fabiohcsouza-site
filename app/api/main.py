"""The routers of each site. The first of each list is its Pages router: the sitemap's list (app.api.routes.seo)."""

from fastapi import APIRouter

from .pages import Pages
from .routes import blog, contact, newsletter, portfolio, seo

SITES: dict[str, list[APIRouter]] = {
    "portfolio": [portfolio.router, seo.router, contact.router],
    "blog": [blog.router, blog.api, seo.router, seo.feed, newsletter.router, newsletter.api],
}
PAGES: dict[str, Pages] = {"portfolio": portfolio.router, "blog": blog.router}
