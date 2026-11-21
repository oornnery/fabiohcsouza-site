"""Markdown -> safe HTML for posts.

Raw HTML in Markdown is disabled (no XSS through content), links are limited to http(s)/mailto/relative,
h2/h3 get stable ids (for the table of contents), code blocks are highlighted by Pygments with CSS classes.
A fence like ```python run.py renders the file name above the code. Images under /assets/ get their width and
height (no layout shift) and are served as WebP when `python -m app images` has written one next to the original."""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from mdit_py_plugins.footnote import footnote_plugin
from pydantic import BaseModel, ConfigDict, Field
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from ..core.config import STATIC

_FORMATTER = HtmlFormatter(nowrap=True, classprefix="hl-")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:80] or "section"


def _highlight(code: str, lang: str, _attrs: str) -> str:
    try:
        return highlight(code, get_lexer_by_name(lang), _FORMATTER) if lang else escapeHtml(code)
    except ClassNotFound:
        return escapeHtml(code)


def _validate_link(url: str) -> bool:
    url = url.strip().lower()
    return url.startswith(("http://", "https://", "mailto:", "/", "#", "./", "../")) or ":" not in url.split("/")[0]


@dataclass
class Rendered:
    html: str
    toc: list[tuple[int, str, str]] = field(default_factory=list)  # (level, id, text)
    words: int = 0


class _Markdown(MarkdownIt):
    def validateLink(self, url: str) -> bool:  # noqa: N802 — markdown-it's name
        return _validate_link(url)


def _md() -> MarkdownIt:
    md = _Markdown("commonmark", {"html": False, "linkify": False, "typographer": True, "highlight": _highlight})
    md.enable("table").enable("strikethrough").use(footnote_plugin)

    def fence(renderer, tokens, idx, options, env):  # noqa: ANN001
        tok = tokens[idx]
        info = tok.info.strip().split(maxsplit=1)
        lang = info[0] if info else ""
        name = info[1] if len(info) > 1 else ""
        body = _highlight(tok.content, lang, "")
        head = f'<div class="code-name">{escapeHtml(name)}</div>' if name else ""
        cls = f' class="language-{escapeHtml(lang)}"' if lang else ""
        return f'<figure class="code">{head}<pre><code{cls}>{body}</code></pre></figure>\n'

    md.add_render_rule("fence", fence)

    def heading_open(renderer, tokens, idx, options, env):  # noqa: ANN001
        tok = tokens[idx]
        if tok.tag in ("h2", "h3"):
            inline = tokens[idx + 1]
            text = "".join(c.content for c in (inline.children or []) if c.type in ("text", "code_inline")) or inline.content
            base, n = slugify(text), 2
            hid = base
            while hid in env["ids"]:
                hid, n = f"{base}-{n}", n + 1
            env["ids"].add(hid)
            env["toc"].append((int(tok.tag[1]), hid, text))
            tok.attrSet("id", hid)
        return renderer.renderToken(tokens, idx, options, env)

    md.add_render_rule("heading_open", heading_open)

    def link_open(renderer, tokens, idx, options, env):  # noqa: ANN001
        tok = tokens[idx]
        if (tok.attrGet("href") or "").startswith(("http://", "https://")):
            tok.attrSet("rel", "noopener noreferrer")
        return renderer.renderToken(tokens, idx, options, env)

    md.add_render_rule("link_open", link_open)

    def image(renderer, tokens, idx, options, env):  # noqa: ANN001
        # images sit below the fold of a post: fetched when the reader gets near them, decoded off the main thread
        tok = tokens[idx]
        tok.attrSet("loading", "lazy")
        tok.attrSet("decoding", "async")
        src = str(tok.attrGet("src") or "")
        if file := _local_image(src, env.get("media")):
            if file.with_suffix(".webp").is_file():  # `python -m app images` wrote a lighter copy
                file = file.with_suffix(".webp")
                src = src.rsplit(".", 1)[0] + ".webp"
            tok.attrSet("src", src if src.startswith("/") else f"{env['media'][1]}/{file.name}")
            from PIL import Image

            with Image.open(file) as im:
                tok.attrSet("width", str(im.width))
                tok.attrSet("height", str(im.height))
        return renderer.image(tokens, idx, options, env)

    md.add_render_rule("image", image)

    def cell_open(renderer, tokens, idx, options, env):  # noqa: ANN001
        # table alignment comes as style="text-align:…"; the CSP forbids inline styles, so it becomes a class
        tok = tokens[idx]
        style = tok.attrGet("style") or ""
        if "text-align:" in style:
            tok.attrs.pop("style", None)
            tok.attrSet("class", "ta-" + style.split(":", 1)[1].strip().rstrip(";"))
        return renderer.renderToken(tokens, idx, options, env)

    md.add_render_rule("th_open", cell_open)
    md.add_render_rule("td_open", cell_open)
    return md


_MD = _md()
IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif")


def media(folder: Path, kind: str) -> tuple[Path, str]:
    """A content folder's assets/ and the URL they are served at (app.api.routes.seo.media): /media/<kind>/<slug>."""
    return folder / "assets", f"/media/{kind}/{folder.name}"


def _local_image(src: str, media: tuple[Path, str] | None) -> Path | None:
    """The file behind an image of this site: /assets/… in static/, or `assets/<name>` in the content folder being
    rendered (served at its media URL). Nothing outside those folders is opened."""
    name = src.removeprefix("assets/")
    if src.startswith("/assets/"):
        root, file = STATIC, (STATIC / src.lstrip("/")).resolve()
    elif media and src.startswith("assets/") and "/" not in name and ":" not in name:
        root, file = media[0], (media[0] / name).resolve()
    else:
        return None
    ok = file.is_relative_to(root) and file.suffix.lower() in IMAGES and file.is_file()
    return file if ok else None


def render(text: str, media: tuple[Path, str] | None = None) -> Rendered:
    """`media`: (the content folder's assets/, its URL) when the text has images of its own: `![alt](assets/x.png)`."""
    env: dict = {"toc": [], "ids": set(), "media": media}
    html = _MD.render(text, env)
    return Rendered(html=html, toc=env["toc"], words=len(re.findall(r"\w+", text)))


def render_inline(text: str) -> str:
    """One line of Markdown (links, emphasis, code) without a wrapping <p>."""
    return _MD.renderInline(text)



# ---- what posts and projects share in their front matter

SLUG = re.compile(r"^[a-z0-9-]{1,80}$")  # a folder name in content/: the address of the page

# old posts use Portuguese tag names: one tag vocabulary for both languages
TAG_ALIASES = {
    "projetos": "projects", "componentes": "components", "acessibilidade": "accessibility",
    "aprendizado": "learning", "notas": "notes", "redes": "networking", "seguranca": "security",
}  # fmt: skip


def tag(t: str) -> str:
    t = slugify(str(t))
    return TAG_ALIASES.get(t, t)


class Translation(BaseModel):
    """The frontmatter of <slug>.en.md: the English texts of a post or work written in Portuguese."""

    model_config = ConfigDict(extra="ignore", frozen=True)
    title: str = Field(min_length=1, max_length=200)
    summary: str = ""
    goal: str = ""
