"""content/posts/: the blog's posts, read with the rest of content/ (app.content). One folder per post:

    <slug>/<slug>.md      in English (the default): front matter + body
    <slug>/<slug>.pt.md   in Portuguese. Next to <slug>.md it holds only title, summary, goal + body; alone, the post
                          is written in Portuguese only and this file has the whole front matter

Front matter: title, summary, goal, created, updated (the last edit), status (`published` goes live; `draft`, the
default, shows only in development), tags, read, repo, image (the share image, 1200x630, a file in the folder),
type (`project` also lists it under Projects > Open Source), series + part (this post is part <part> of the post
<series>), project (the slug of a project it is about).
Images go in the post's folder, next to the .md, and are written by name: ![alt](shot.png)."""

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import frontmatter
from pydantic import BaseModel, ConfigDict, Field

from ..core.i18n import LANGS
from ..utils import markdown
from ..utils.markdown import SLUG, Translation, tag
from .projects import Project


class Front(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    title: str = Field(min_length=1, max_length=200)
    created: dt.date
    updated: dt.date | None = None
    status: Literal["published", "draft"] = "draft"
    type: str = "post"
    summary: str = ""
    goal: str = ""
    tags: list[str] = []
    read: int | None = None
    repo: str | None = None
    image: str | None = None  # share image (1200x630) in the post's assets/: `assets/cover.png`
    series: str | None = None  # the slug of the post this one is a part of
    part: int = 0  # its position in that series
    project: str | None = None  # the slug of a project (content/projects/) this post is about


@dataclass
class Version:
    title: str
    summary: str
    goal: str
    html: str
    toc: list[tuple[int, str, str]]
    words: int


@dataclass
class Post:
    slug: str
    created: dt.date
    updated: dt.date
    status: str
    type: str
    tags: list[str]
    read: int
    repo: str | None
    versions: dict[str, Version]
    series: Post | None = field(default=None, repr=False, compare=False)  # the series index this post is a part of
    order: int = 0
    image: str | None = None
    parts: list[Post] = field(default_factory=list)
    source: str = "en"  # the language it was written in
    project: str | None = None

    def v(self, lang: str) -> Version:
        return self.versions.get(lang) or self.versions[self.source]

    def translated(self, lang: str) -> bool:
        return lang in self.versions

    @property
    def published(self) -> bool:
        return self.status == "published"


@dataclass
class Posts:
    posts: list[Post]  # published (or all in dev), newest first, without the `type: project` ones
    project_posts: list[Post]
    by_slug: dict[str, Post]
    tags: list[tuple[str, int]]  # (tag, count), most used first

    def neighbors(self, post: Post) -> dict[str, Post | None]:
        """{"prev": older, "next": newer} around a post in the timeline; none for `type: project` posts.
        A part of a series gets the part before and the part after instead."""
        line = post.series.parts if post.series else self.posts[::-1]
        i = line.index(post) if post in line else -1
        return {"prev": line[i - 1] if i > 0 else None, "next": line[i + 1] if 0 <= i < len(line) - 1 else None}

    def about(self, project: str) -> list[Post]:
        """The posts about a project, newest first."""
        return [p for p in self.posts if p.project == project]

    def years(self) -> dict[int, list[Post]]:
        out: dict[int, list[Post]] = {}
        for p in self.posts:
            out.setdefault(p.created.year, []).append(p)
        return out


def _version(front: Front | Translation, body: str, folder: Path) -> Version:
    r = markdown.render(body, markdown.media(folder, "posts"))
    return Version(front.title, front.summary, front.goal, r.html, r.toc, r.words)


def demo_posts(path: Path, n: int) -> list[Post]:
    """The first N fake posts from dev/demo-posts.json, to exercise pagination, Timeline and filters in development.
    Never in production (see get)."""
    out = []
    for d in json.loads(path.read_text(encoding="utf-8"))["posts"][:n]:
        versions = {}
        for lang in LANGS:
            r = markdown.render(d[lang]["body"])
            versions[lang] = Version(d[lang]["title"], d[lang]["summary"], "", r.html, r.toc, r.words)
        created = dt.date.fromisoformat(d["created"])
        out.append(Post(slug=d["slug"], created=created, updated=created, status="published", type="post",
                        tags=d["tags"], read=d["read"], repo=None, versions=versions))
    return out


def load(root: Path, include_drafts: bool = False, demo: int = 0, demo_file: Path | None = None) -> Posts:
    by_slug: dict[str, Post] = {}
    parent: dict[str, str] = {}  # part slug -> slug of its series
    folder_ = root / "posts"
    for folder in sorted(p for p in folder_.iterdir() if p.is_dir()) if folder_.is_dir() else []:
        slug = folder.name
        if not SLUG.match(slug):
            raise ValueError(f"{folder}: bad folder name (use a-z, 0-9 and -)")
        en, pt = folder / f"{slug}.md", folder / f"{slug}.pt.md"
        if not (main := en if en.exists() else pt if pt.exists() else None):
            raise ValueError(f"{folder}: needs {slug}.md (English) or {slug}.pt.md (Portuguese)")
        doc = frontmatter.loads(main.read_text(encoding="utf-8"))
        front = Front.model_validate(doc.metadata)
        source = "en" if main == en else "pt"
        versions = {source: _version(front, doc.content, folder)}
        if source == "en" and pt.exists():
            tr = frontmatter.loads(pt.read_text(encoding="utf-8"))
            versions["pt"] = _version(Translation.model_validate(tr.metadata), tr.content, folder)
        if front.image and not (front.image.startswith("assets/") and (folder / front.image).is_file()):
            raise ValueError(f"{folder}: image {front.image!r} is not in the post's assets/")
        by_slug[slug] = Post(
            slug=slug, created=front.created, updated=max(front.updated or front.created, front.created),
            status=front.status, type=front.type, tags=sorted({tag(t) for t in front.tags} - {"projects"}),
            read=front.read or max(1, round(versions[source].words / 220)), repo=front.repo, versions=versions,
            order=front.part, image=front.image and f"{markdown.media(folder, 'posts')[1]}/{front.image.removeprefix('assets/')}",
            source=source, project=front.project,
        )
        if front.series:
            parent[slug] = front.series
    for slug, series in parent.items():
        if series not in by_slug:
            raise ValueError(f"posts/{slug}: series {series!r} is not a post")
    for post in demo_posts(demo_file, demo) if demo and demo_file else []:
        by_slug[post.slug] = post

    visible = [p for p in by_slug.values() if p.published or include_drafts]
    for p in visible:
        index = by_slug.get(parent.get(p.slug, ""))
        if index in visible:  # a draft index in production: its parts are plain posts
            p.series = index
            index.parts.append(p)
    for p in by_slug.values():
        p.parts.sort(key=lambda x: x.order)
    newest = sorted(visible, key=lambda p: (p.created, p.slug), reverse=True)
    posts = [p for p in newest if p.type != "project"]
    project_posts = [p for p in newest if p.type == "project"]

    counts: dict[str, int] = {}
    for p in posts:
        for t in p.tags:
            counts[t] = counts.get(t, 0) + 1
    return Posts(posts=posts, project_posts=project_posts, by_slug={p.slug: p for p in visible},
                 tags=sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def as_project(p: Post) -> Project:
    """A post with `type: project`, listed with the portfolio's open-source projects."""
    return Project(name=p.v("en").title, desc={lang: p.v(lang).summary for lang in LANGS}, tags=p.tags,
                links={"post": p.slug, **({"repo": p.repo} if p.repo else {})}, year=p.created.year,
                titles={lang: p.v(lang).title for lang in LANGS}, updated=p.updated)
