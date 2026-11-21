"""content/: the source of both sites, read once at start (reload in dev).

    content/site.yml                    owner: name, e-mail, socials (data, not prose)
    content/pages/<name>/<name>.md      a page (about, privacy) in English: front matter fields + Markdown body
    content/pages/<name>/<name>.pt.md   the same page in Portuguese; images in content/pages/<name>/assets/
    content/projects/                   the portfolio's projects (app.content.projects)
    content/posts/                      the blog's posts (app.content.posts)

Both sites read all of it: the portfolio home lists the latest posts, and a `type: project` post is also a project."""

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import frontmatter
import yaml

from ..core.config import Settings
from ..utils import markdown
from . import posts, projects
from .projects import Project


@dataclass
class PageText:
    """A page's texts in one language: frontmatter fields + Markdown body (rendered per request: links depend on
    the site/language/mode, see render_page)."""

    fields: dict[str, str]
    body: str
    folder: Path  # its images are in assets/


@dataclass
class Content:
    site: dict
    pages: dict[str, dict[str, PageText]]  # name -> lang -> text
    open_source: list[Project]
    work: list[Project]
    blog: posts.Posts

    def page(self, name: str, lang: str, url: Callable[..., str]) -> tuple[dict[str, str], str]:
        """(fields, body) of content/pages/<name> as HTML in `lang` (falls back to English). `url` is
        app.utils.web.Page.url: (/x) links go to the portfolio, (blog:/x) to the blog, right in every language and mode."""
        texts = self.pages[name]
        return render_page(texts.get(lang) or texts["en"], url)

    @property
    def project_pages(self) -> list[Project]:
        """The projects with a page of their own, /projects/<slug>."""
        return [p for p in [*self.work, *self.open_source] if p.slug]

    def project_page(self, slug: str) -> Project | None:
        return next((p for p in self.project_pages if p.slug == slug), None)


def load(root: Path, include_drafts: bool = False) -> Content:
    pages: dict[str, dict[str, PageText]] = {}
    for path in sorted((root / "pages").glob("*/*.md")):
        name = path.parent.name
        lang = "pt" if path.name == f"{name}.pt.md" else "en"
        doc = frontmatter.loads(path.read_text(encoding="utf-8"))
        pages.setdefault(name, {})[lang] = PageText({k: str(v) for k, v in doc.metadata.items()}, doc.content, path.parent)
    all_projects = projects.load(root, include_drafts)
    blog = posts.load(root, include_drafts)
    if missing := {p.project for p in blog.by_slug.values() if p.project} - {p.slug for p in all_projects}:
        raise ValueError(f"posts about projects that don't exist: {sorted(missing)}")
    open_source = [*map(posts.as_project, blog.project_posts), *(p for p in all_projects if p.kind == "open_source")]
    return Content(
        site=yaml.safe_load((root / "site.yml").read_text(encoding="utf-8")), pages=pages,
        open_source=projects.newest(open_source), work=[p for p in all_projects if p.kind == "work"], blog=blog,
    )


LINK = re.compile(r"\]\((blog:)?(/[^)\s]*)\)")


def _links(md: str, url: Callable[..., str]) -> str:
    """(/x) to the portfolio and (blog:/x) to the blog, in the page's language."""
    return LINK.sub(lambda m: f"]({url(m.group(2), site='blog' if m.group(1) else 'portfolio')})", md)


def render_page(text: PageText, url: Callable[..., str]) -> tuple[dict[str, str], str]:
    fields = {k: markdown.render_inline(_links(v, url)) for k, v in text.fields.items()}
    return fields, markdown.render(_links(text.body, url), markdown.media(text.folder, "pages")).html


_cache: dict[tuple, tuple[float, float, Content]] = {}  # key -> (files' mtime, checked at, content)


def _stamp(root: Path) -> float:
    return max((p.stat().st_mtime for p in root.rglob("*") if p.is_file()), default=0.0)


def get(settings: Settings, drafts: bool = False) -> Content:
    """The content, loaded once per process. In development it reloads when a file in content/ changes (checked at
    most once a second) and shows drafts (`drafts`)."""
    key = (settings.content_dir, drafts)
    cached = _cache.get(key)
    if cached and (settings.production or time.monotonic() - cached[1] < 1):
        return cached[2]
    stamp = _stamp(settings.content_dir)
    content = cached[2] if cached and cached[0] == stamp else load(settings.content_dir, drafts)
    _cache[key] = (stamp, time.monotonic(), content)
    return content
