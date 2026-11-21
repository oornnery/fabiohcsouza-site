"""Command line: `python -m app <command>` (in production: docker compose exec portfolio|blog python -m app …).

    serve [--reload]            run the sites (http://portfolio.localhost:8000, http://blog.localhost:8000)
    purge                       apply the data retention rules now
    leads [--last N]            the latest contact messages
    stats                       how many contact messages, and whether e-mail is on
    subscribers                 how many newsletter subscribers
    send-post <slug> [--send]   e-mail a published post to the subscribers (a dry run without --send)
    projects-dates              set each project's `updated` to the date of its last commit on GitHub
    i18n                        collect the strings to translate into app/locales/*/messages.po
    images                      a WebP next to each PNG/JPEG in content/ (the pages then serve it)
"""

import argparse
import asyncio
import contextlib
import os
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx
from sqlalchemy import Engine
from sqlmodel import Session

from . import content, crud
from .content.posts import Post
from .content.projects import GITHUB, folders, set_updated
from .core import i18n as lang_catalog
from .core import security
from .core.config import ROOT, Settings, get_settings
from .core.db import make_engine
from .models import Subscriber
from .utils import mail

UNSUBSCRIBE_HEADERS = {"List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}


def serve(settings: Settings, args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("app.main:create_app", factory=True, host=settings.host, port=settings.port, reload=args.reload,
                proxy_headers=False, server_header=False, reload_dirs=["app", "content"] if args.reload else None)
    return 0


def purge(settings: Settings, _args: argparse.Namespace, engine: Engine) -> int:
    print(f"{crud.purge(engine, settings.sites)} rows removed")
    return 0


# ---- contact

def leads(_settings: Settings, args: argparse.Namespace, engine: Engine) -> int:
    with Session(engine) as s:
        for lead in crud.latest_leads(s, args.last):
            print(f"#{lead.id} {lead.created_at} [{lead.lang}] {lead.name} <{lead.email}> {lead.phone or ''}")
            print(f"   {lead.subject}\n   {lead.message[:300].replace(chr(10), ' ')}\n")
    return 0


def stats(settings: Settings, _args: argparse.Namespace, engine: Engine) -> int:
    with Session(engine) as s:
        print(f"leads        {crud.count_leads(s)}")
    print(f"e-mail       {settings.mail_provider or 'off (only logged)'}")
    return 0


# ---- newsletter

def subscribers(_settings: Settings, _args: argparse.Namespace, engine: Engine) -> int:
    with Session(engine) as s:
        confirmed, unconfirmed = crud.subscriber_counts(s)
    print(f"confirmed    {confirmed}\nunconfirmed  {unconfirmed}")
    return 0


def post_message(settings: Settings, post: Post, sub: Subscriber) -> tuple[str, str]:
    """(subject, body) of a post for one subscriber, in their language when the post has it."""
    v, lang = post.v(sub.lang), sub.lang if post.translated(sub.lang) else post.source
    return mail.compose("post", sub.lang, title=v.title, summary=v.summary or v.title, blog=settings.site_host("blog"),
                        url=f"{settings.blog_url}{lang_catalog.prefix(lang)}/posts/{post.slug}",
                        unsub=security.link(settings, "/unsubscribe", "unsubscribe", sub))


async def deliver(settings: Settings, engine: Engine, post: Post, todo: list[Subscriber]) -> int:
    """One e-mail per subscriber, each recorded as it goes out; stops at the first refusal.
    shortcut: one SMTP connection per message, fine for hundreds; batch them on one connection beyond that."""
    for n, sub in enumerate(todo, 1):
        unsub = security.link(settings, "/unsubscribe", "unsubscribe", sub)
        try:
            await mail.send_email(settings, sub.email, *post_message(settings, post, sub),
                                  headers={"List-Unsubscribe": f"<{unsub}>", **UNSUBSCRIBE_HEADERS})
        except mail.ProviderError as e:
            print(f"stopped after {n - 1} of {len(todo)}: {e}. Run it again to continue.")
            return 1
        with Session(engine) as s:
            crud.record_delivery(s, post.slug, sub)
    print(f"sent {post.slug!r} to {len(todo)} subscriber(s)")
    return 0


def send_post(settings: Settings, args: argparse.Namespace, engine: Engine) -> int:
    """Without --send: who would get it and the e-mail as it will look. With --send: send it."""
    post = content.get(settings).blog.by_slug.get(args.slug)  # published posts only, never drafts
    if post is None:
        print(f"{args.slug!r} is not a published post")
        return 1
    with Session(engine) as s:
        todo = crud.waiting_for(s, post.slug)
    if args.send:
        return asyncio.run(deliver(settings, engine, post, todo))
    print(f"{len(todo)} subscriber(s) would get {post.slug!r}. Add --send to send.")
    if todo:
        print("\nSubject: {}\n\n{}".format(*post_message(settings, post, todo[0])))
    return 0


# ---- content

def last_commit(repo: str, headers: dict[str, str]) -> str:
    """The date (YYYY-MM-DD) of the last commit on the default branch of `owner/name`."""
    r = httpx.get(f"https://api.github.com/repos/{repo}/commits", params={"per_page": 1}, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()[0]["commit"]["committer"]["date"][:10]


def projects_dates(settings: Settings, _args: argparse.Namespace) -> int:
    """Sets `updated` of each project with a GitHub repo to the date of its last commit. GITHUB_TOKEN (optional, from
    the environment) lets it read private repos and lifts the limit of 60 requests an hour."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {token}"} if token else {})}
    for folder in folders(settings.content_dir):
        path = folder / f"{folder.name}.md"
        text = path.read_text(encoding="utf-8")
        if not (m := GITHUB.search(text)):
            print(f"{folder.name}: no GitHub repo, set `updated` by hand")
            continue
        try:
            day = last_commit(m[1], headers)
        except (httpx.HTTPError, LookupError, ValueError) as e:
            print(f"{folder.name}: skipped ({type(e).__name__})")
            continue
        if (new := set_updated(text, day)) != text:
            path.write_text(new, encoding="utf-8")
        print(f"{folder.name}: {day}")
    return 0


def i18n(_settings: Settings, _args: argparse.Namespace) -> int:
    """pybabel extract (babel.cfg) + update: new strings show up untranslated in the .po, removed ones go obsolete."""
    from babel.messages.frontend import CommandLineInterface

    pot = Path(tempfile.mkdtemp()) / "messages.pot"  # intermediate, not kept
    cli = CommandLineInterface()
    with contextlib.chdir(ROOT):  # file references in the .po stay relative (app/…)
        cli.run(["pybabel", "-q", "extract", "-F", "babel.cfg", "--no-wrap", "--sort-by-file", "--omit-header", "-o", str(pot), "."])
    for lang in lang_catalog.LANGS[1:]:
        cli.run(["pybabel", "-q", "update", "-i", str(pot), "-d", str(lang_catalog.LOCALES), "-l", lang_catalog.locale(lang),
                 "--no-wrap", "--omit-header", "--ignore-obsolete"])
    print(f"updated {', '.join(lang_catalog.locale(lang) for lang in lang_catalog.LANGS[1:])}: "
          "translate the empty msgstr lines, then run the tests")
    return 0


def images(settings: Settings, _args: argparse.Namespace) -> int:
    """A WebP next to each PNG/JPEG in content/. Originals stay (share images must be PNG/JPEG)."""
    from PIL import Image

    root = settings.content_dir
    for src in sorted(p for p in root.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")):
        out = src.with_suffix(".webp")
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            with Image.open(src) as im:
                im.save(out, "WEBP", quality=82, method=6)
            print(f"{src.relative_to(root)}: {src.stat().st_size // 1024} KB -> {out.stat().st_size // 1024} KB")
    return 0


# name -> (handler, needs the database, arguments)
COMMANDS: dict[str, tuple[Callable[..., int], bool, list[tuple[tuple, dict]]]] = {
    "serve": (serve, False, [(("--reload",), {"action": "store_true"})]),
    "purge": (purge, True, []),
    "leads": (leads, True, [(("--last",), {"type": int, "default": 20})]),
    "stats": (stats, True, []),
    "subscribers": (subscribers, True, []),
    "send-post": (send_post, True, [(("slug",), {}), (("--send",), {"action": "store_true"})]),
    "projects-dates": (projects_dates, False, []),
    "i18n": (i18n, False, []),
    "images": (images, False, []),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, (_fn, _db, arguments) in COMMANDS.items():
        cmd = sub.add_parser(name)
        for flags, options in arguments:
            cmd.add_argument(*flags, **options)
    args = parser.parse_args(argv)
    settings = get_settings()
    fn, needs_db, _ = COMMANDS[args.cmd]
    return fn(settings, args, make_engine(settings.database_url)) if needs_db else fn(settings, args)


if __name__ == "__main__":
    sys.exit(main())
