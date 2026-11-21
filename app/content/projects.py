"""content/projects/<slug>/: the projects on the portfolio, each with its own page at /projects/<slug>.

    <slug>/<slug>.md      in English (the default): front matter + the page's text
    <slug>/<slug>.pt.md   in Portuguese (optional): title, summary + the page's text
    <slug>/assets/        its images, written as ![alt](assets/x.png)

Front matter: title, summary (the short description, in lists), kind (work | open_source), updated (the date of the
last commit: `python -m app projects-dates`), year, tags, repo/site/post links. Newest first: by `updated`, then name."""

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import frontmatter
from pydantic import BaseModel, ConfigDict, Field

from ..core.i18n import LANGS
from ..utils import markdown
from ..utils.markdown import SLUG, Translation, tag


@dataclass
class Project:
    name: str  # English title
    desc: dict[str, str]
    tags: list[str]
    links: dict[str, str]
    year: int | None = None
    kind: Literal["open_source", "work"] = "open_source"
    titles: dict[str, str] = field(default_factory=dict)
    slug: str | None = None  # its page, /projects/<slug> (None: a blog post with `type: project`, which links to the post)
    updated: dt.date | None = None
    html: dict[str, str] = field(default_factory=dict)  # lang -> the page's text

    def title(self, lang: str) -> str:
        return self.titles.get(lang) or self.name


class ProjectFront(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    title: str = Field(min_length=1, max_length=120)
    summary: str = ""
    kind: Literal["open_source", "work"] = "open_source"
    year: int | None = None
    updated: dt.date | None = None
    status: Literal["published", "draft"] = "published"
    tags: list[str] = []
    repo: str | None = None
    site: str | None = None
    post: str | None = None


def newest(projects: list[Project]) -> list[Project]:
    """Last updated first; projects without a date after the others."""
    return sorted(projects, key=lambda p: (p.updated is None, -(p.updated or dt.date.min).toordinal(), p.name.lower()))


def _render(body: str, folder: Path) -> str:
    return markdown.render(body, markdown.media(folder, "projects")).html if body.strip() else ""


def _read(folder: Path, include_drafts: bool) -> Project | None:
    slug = folder.name
    if not SLUG.match(slug):
        raise ValueError(f"{folder}: bad folder name (use a-z, 0-9 and -)")
    doc = frontmatter.loads((folder / f"{slug}.md").read_text(encoding="utf-8"))
    front = ProjectFront.model_validate(doc.metadata)
    if front.status != "published" and not include_drafts:
        return None
    body = _render(doc.content, folder)
    titles, desc, html = dict.fromkeys(LANGS, front.title), dict.fromkeys(LANGS, front.summary), dict.fromkeys(LANGS, body)
    pt = folder / f"{slug}.pt.md"
    if pt.exists():  # the Portuguese version; what it leaves out stays in English
        pt_doc = frontmatter.loads(pt.read_text(encoding="utf-8"))
        tr = Translation.model_validate(pt_doc.metadata)
        titles["pt"], desc["pt"] = tr.title, tr.summary or front.summary
        html["pt"] = _render(pt_doc.content, folder) or html["pt"]
    links = {k: v for k in ("repo", "site", "post") if (v := getattr(front, k))}
    return Project(name=front.title, desc=desc, tags=[tag(t) for t in front.tags], links=links, year=front.year,
                   kind=front.kind, titles=titles, slug=slug, updated=front.updated, html=html)


def folders(root: Path) -> list[Path]:
    return sorted(p for p in (root / "projects").iterdir() if p.is_dir())


def load(root: Path, include_drafts: bool = False) -> list[Project]:
    """Every project, newest first. A draft shows only in development."""
    return newest([p for folder in folders(root) if (p := _read(folder, include_drafts))])


# ---- the `updated` date (python -m app projects-dates)

GITHUB = re.compile(r"^repo:\s*https://github\.com/([\w.-]+/[\w.-]+?)/?\s*$", re.M)


def set_updated(text: str, day: str) -> str:
    """`text` (a project's .md) with `updated: <day>` in its front matter, replaced or added."""
    head, sep, body = text.removeprefix("---\n").partition("\n---\n")
    lines = [line for line in head.split("\n") if not line.startswith("updated:")]
    return "---\n" + "\n".join([*lines, f"updated: {day}"]) + sep + body
