"""The public pages of a site, declared once: each one becomes its GET route, an entry in the sitemap, a page the
tests open in both languages and, when it has a `menu` label, a link in the header/footer.

Only what is registered here is listed. Routes that are not pages (redirects, /api) use the plain
router decorators and never reach the sitemap.

    router = Pages("blog", dependencies=[...])
    router.add("/posts", "blog/posts.html", menu="Posts")             # rendered as is
    router.add("/posts/{slug}", "blog/post.html", each=…, context=…)  # one page per value of `each`
    router.add("/contact", "portfolio/contact.html", endpoint=contact_page, menu="Contact")  # its own endpoint"""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..content import Content
from ..utils.web import template_globals, templates
from .deps import ContentDep, render_page

type Context = Callable[..., dict]
MENUS: dict[str, list[MenuItem]] = {}  # site -> menu, for layout/header.html and footer.html
template_globals(templates).update(menus=MENUS)  # (content, **path params) -> extra template values


@dataclass(frozen=True)
class MenuItem:
    label: str
    path: str
    site: str  # the site the link goes to
    header: bool = True
    footer: bool = True
    flag: str = ""  # a Settings switch that hides this link when off ("newsletter")


@dataclass(frozen=True)
class PublicPage:
    path: str  # "/projects" or "/posts/{slug}"
    template: str
    context: Context | None = None
    each: Callable[[Content], list[dict]] | None = None  # path params of every page, for the sitemap and the tests
    lastmod: Callable[..., date | None] | None = None  # (content, **path params) -> date, for the sitemap
    langs: Callable[..., list[str]] | None = None  # (content, **path params) -> languages it exists in (default: all)
    nav: str = ""  # nav item marked current (default: the path)
    sitemap: bool = True
    flag: str = ""  # a Settings switch that takes this page out of the sitemap when off

    def values(self, c: Content, **params: str) -> dict:
        return self.context(c, **params) if self.context else {}

    def __call__(self, request: Request, c: ContentDep):
        """The page's own endpoint: its template with `context`'s values."""
        return render_page(request, self.template, nav=self.nav, **self.values(c, **request.path_params))


class Pages(APIRouter):
    def __init__(self, site: str, **kwargs):
        super().__init__(default_response_class=HTMLResponse, **kwargs)
        self.site = site
        self.pages: list[PublicPage] = []
        self.menu: list[MenuItem] = []
        MENUS[site] = self.menu

    def add(self, path: str, template: str, *, endpoint: Callable | None = None, menu: str = "", header: bool = True,
            footer: bool = True, **options) -> None:
        page = PublicPage(path, template, **options)
        self.pages.append(page)
        if menu:
            self.link(menu, path, header=header, footer=footer, flag=page.flag)
        self.add_api_route(path, endpoint or page, methods=["GET"], name=path)

    def link(self, label: str, path: str, site: str = "", header: bool = True, footer: bool = True, flag: str = "") -> None:
        """A menu entry that is not a page of this site: the other site's home, the RSS feed."""
        self.menu.append(MenuItem(label, path, site or self.site, header, footer, flag))

    def urls(self, c: Content) -> Iterator[tuple[PublicPage, str, dict]]:
        """Every concrete page: (page, path, path params)."""
        for page in self.pages:
            for params in page.each(c) if page.each else [{}]:
                yield page, page.path.format(**params), params
