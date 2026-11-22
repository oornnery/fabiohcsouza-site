"""The blog: every page in both languages, posts, series, tags, feed, and the newsletter."""

import re

import pytest
from sqlmodel import Session, select

from app import content
from app.api.routes import blog as routes
from app.models import Delivery, Subscriber

from .conftest import B_ORIGIN, make_settings

# every registered page (app.api.pages), posts included: a new page is tested without touching this file
_c = content.get(make_settings())
PAGES = [path for _, path, _ in routes.router.urls(_c)]


@pytest.mark.parametrize("lang", ["", "/pt"])
@pytest.mark.parametrize("path", PAGES)
def test_blog_pages(blog, path, lang):
    assert blog.get(lang + path).status_code == 200


def test_seo_files(portfolio, blog):
    assert "Sitemap: http://portfolio.localhost:8000/sitemap.xml" in portfolio.get("/robots.txt").text
    sm = blog.get("/sitemap.xml").text
    assert "/posts/link-or-button" in sm and 'hreflang="pt-BR"' in sm
    rss = blog.get("/rss.xml")
    assert rss.headers["content-type"].startswith("application/xml") and "<item>" in rss.text


def test_json_ld_is_valid_and_script_safe(blog):
    import json

    html = blog.get("/posts/link-or-button").text
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert blocks
    data = json.loads(blocks[0])
    assert any(n["@type"] == "BlogPosting" for n in data["@graph"])


def test_post_navigation_and_toc(blog):
    html = blog.get("/posts/type-hints-mypyc-cython").text  # draft: visible in development only
    assert 'class="toc"' in html and 'href="#the-three-algorithms"' in html


def test_every_registered_page_is_in_the_sitemap(blog):
    sitemap = blog.get("/sitemap.xml").text
    for page, path, _ in routes.router.urls(_c):
        assert (f"{path}</loc>" in sitemap) == page.sitemap or path == "/"


def test_tag_pages_are_rendered_by_the_server(blog):
    html = blog.get("/tags/python").text
    assert "<h1>#python</h1>" in html and 'href="/tags/python" aria-current="page"' in html
    assert "/posts/file-paths-with-pathlib" in html and "/posts/link-or-button" not in html
    assert blog.get("/tags/no-such-tag").status_code == 404
    assert "/tags/python</loc>" in blog.get("/sitemap.xml").text


def test_share_links_work_without_javascript(blog):
    html = blog.get("/pt/posts/link-or-button").text
    assert 'href="https://www.linkedin.com/sharing/share-offsite/?url=http%3A//blog.localhost%3A8000/pt/posts/link-or-button"' in html


def test_rss_carries_the_whole_post(blog):
    rss = blog.get("/rss.xml").text
    assert "<content:encoded>" in rss and "<lastBuildDate>" in rss


def test_post_in_one_language_has_one_canonical_url_and_its_share_image(settings, tmp_path):
    """A post without .en.md is the same Portuguese text at / and /pt: only /pt is canonical and listed."""
    import shutil

    from fastapi.testclient import TestClient

    from app.main import create_app

    root = tmp_path / "content"
    shutil.copytree(settings.content_dir, root)
    front = "---\ntitle: Só em português\ncreated: 2026-01-01\nstatus: published\nimage: assets/cover.png\n---\n"
    (root / "posts" / "so-pt").mkdir()
    (root / "posts" / "so-pt" / "so-pt.pt.md").write_text(front + "Texto.\n\n![Uma imagem](assets/shot.png)\n", encoding="utf-8")
    from PIL import Image

    (root / "posts" / "so-pt" / "assets").mkdir()
    Image.new("RGB", (1200, 630)).save(root / "posts" / "so-pt" / "assets" / "cover.png")
    Image.new("RGB", (40, 20)).save(root / "posts" / "so-pt" / "assets" / "shot.png")
    client = TestClient(create_app(settings.model_copy(update={"content_dir": root})), base_url="http://blog.localhost:8000")
    html = client.get("/posts/so-pt").text
    assert '<link rel="canonical" href="http://blog.localhost:8000/pt/posts/so-pt">' in html
    assert 'hreflang="en"' not in html and 'hreflang="x-default" href="http://blog.localhost:8000/pt/posts/so-pt"' in html
    assert '<meta property="og:image" content="http://blog.localhost:8000/media/posts/so-pt/cover.png">' in html  # its own
    assert 'src="/media/posts/so-pt/shot.png" alt="Uma imagem" loading="lazy" decoding="async" width="40" height="20"' in html
    assert client.get("/media/posts/so-pt/shot.png").headers["content-type"] == "image/png"
    for bad in ("/media/posts/so-pt/so-pt.pt.md", "/media/posts/..%2F..%2Fsite.yml/x.png", "/media/secret/so-pt/shot.png"):
        assert client.get(bad).status_code == 404, bad
    assert 'og:image" content="http://blog.localhost:8000/og.png"' in client.get("/posts/link-or-button").text
    sitemap = client.get("/sitemap.xml").text
    assert "/pt/posts/so-pt</loc>" in sitemap and "8000/posts/so-pt</loc>" not in sitemap
    assert "<link>http://blog.localhost:8000/pt/posts/so-pt</link>" in client.get("/rss.xml").text


def test_series_part_shows_its_series(blog):
    html = blog.get("/posts/form-with-plain-post").text  # part 2 of python-meets-the-web
    assert 'href="/posts/python-meets-the-web">' in html and "part 2 of 3" in html
    assert 'href="/posts/form-with-plain-post" class="active" aria-current="page"' in html
    assert 'href="/posts/fastapi-route-from-code-to-response" rel="prev"' in html  # the series' order, not the blog's
    assert 'href="/posts/jinja-list-and-partial" rel="next"' in html
    assert "All parts →" in html
    badge = '<a class="badge" href="/posts/python-meets-the-web">Python meets the web</a>'  # the name leads to the series
    assert badge in blog.get("/posts").text and badge in blog.get("/timeline").text
    assert 'class="badge"' not in blog.get("/posts/python-meets-the-web").text  # its own parts need no label



# ---- newsletter

def _outbox(monkeypatch) -> list[tuple[str, str, str, dict]]:
    from app.utils import mail

    sent = []

    async def fake(settings, to, subject, text, *, reply_to=None, headers=None):
        sent.append((to, subject, text, headers or {}))

    monkeypatch.setattr(mail, "send_email", fake)
    return sent


def _link(text: str) -> str:
    m = re.search(r"http://blog\.localhost:8000(\S+)", text)
    assert m
    return m.group(1)


def test_like_counts_and_answers_json_or_redirect(blog):
    origin = {"Origin": B_ORIGIN}
    assert 'data-like-count>0<' in blog.get("/posts/hello-world").text
    r = blog.post("/api/posts/hello-world/like", headers={**origin, "Accept": "application/json"})
    assert r.status_code == 200 and r.json() == {"likes": 1}
    r = blog.post("/pt/api/posts/hello-world/like", headers=origin, follow_redirects=False)  # a plain form POST
    assert r.status_code == 303 and r.headers["location"] == "/pt/posts/hello-world#like"
    assert 'data-like-count>2<' in blog.get("/posts/hello-world").text
    assert blog.post("/api/posts/nope/like", headers=origin).status_code == 404
    assert blog.post("/api/posts/hello-world/like").status_code == 403  # no Origin: CSRF guard


def test_like_rate_limit(blog):
    headers = {"Origin": B_ORIGIN, "Accept": "application/json"}
    codes = [blog.post("/api/posts/hello-world/like", headers=headers).status_code for _ in range(routes.LIKE_LIMIT + 1)]
    assert codes[-2] == 200 and codes[-1] == 429


def test_subscribe_confirm_with_a_button(blog, engine, monkeypatch):
    sent = _outbox(monkeypatch)
    r = blog.post("/pt/api/subscribe", json={"email": "Ana@Example.com"}, headers={"Origin": B_ORIGIN})
    assert r.status_code == 201
    assert blog.post("/api/subscribe", json={"email": "ana@example.com"}, headers={"Origin": B_ORIGIN}).status_code == 201  # same answer
    assert len(sent) == 1 and sent[0][0] == "ana@example.com" and sent[0][1] == "Confirme sua inscrição"  # one e-mail, in Portuguese
    link = _link(sent[0][2])
    assert link.startswith("/pt/subscribe/confirm?id=")
    assert "Sim, quero receber" in blog.get(link).text  # a GET only shows the button (mail scanners open links)
    with Session(engine) as s:
        assert s.exec(select(Subscriber)).one().confirmed_at is None
    assert blog.post(link, headers={"Origin": B_ORIGIN}).status_code == 200
    with Session(engine) as s:
        assert s.exec(select(Subscriber)).one().confirmed_at
    assert blog.get(link.replace("&t=", "&t=0")).status_code == 400  # a forged token


def test_send_post_then_one_click_unsubscribe(app, blog, engine, settings, monkeypatch, capsys):
    from argparse import Namespace

    from app.__main__ import send_post

    sent = _outbox(monkeypatch)
    with Session(engine) as s:
        s.add(Subscriber(email="a@x.dev", lang="en", confirmed_at="2026-01-01T00:00:00Z"))
        s.add(Subscriber(email="b@x.dev", lang="pt"))  # never confirmed: gets nothing
        s.commit()

    dry, send = Namespace(slug="link-or-button", send=False), Namespace(slug="link-or-button", send=True)
    assert send_post(settings, dry, engine) == 0 and not sent and "1 subscriber(s) would get" in capsys.readouterr().out
    assert send_post(settings, send, engine) == 0 and send_post(settings, send, engine) == 0  # the second run sends nothing
    assert len(sent) == 1
    to, _subject, text, headers = sent[0]
    assert to == "a@x.dev" and "http://blog.localhost:8000/posts/link-or-button" in text
    assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    unsub = headers["List-Unsubscribe"].strip("<>").removeprefix("http://blog.localhost:8000")
    assert unsub in text
    assert blog.post(unsub, data={"List-Unsubscribe": "One-Click"}).status_code == 200  # a mail client: no Origin
    with Session(engine) as s:
        assert [x.email for x in s.exec(select(Subscriber))] == ["b@x.dev"] and not s.exec(select(Delivery)).all()
    assert blog.post(unsub).status_code == 400  # the address is gone: its link no longer works


def test_unconfirmed_addresses_are_deleted_after_7_days(engine):
    from datetime import timedelta

    from app.core.db import now
    from app.crud import purge

    with Session(engine) as s:
        s.add(Subscriber(email="old@x.dev", created_at=now(timedelta(days=8))))
        s.add(Subscriber(email="new@x.dev"))
        s.add(Subscriber(email="kept@x.dev", created_at=now(timedelta(days=30)), confirmed_at=now(timedelta(days=29))))
        s.commit()
    purge(engine, ("blog",))
    with Session(engine) as s:
        assert sorted(x.email for x in s.exec(select(Subscriber))) == ["kept@x.dev", "new@x.dev"]


def test_post_shows_its_last_edit_and_its_project(blog, portfolio):
    html = blog.get("/pt/posts/reading-a-sip-ladder-488").text  # a draft: visible in development only
    assert "Atualizado em" in html and 'href="http://portfolio.localhost:8000/pt/projects/sipx"' in html
    assert "/posts/reading-a-sip-ladder-488" in portfolio.get("/projects/sipx").text  # the project lists its posts


def test_subscribing_again_resends_only_after_10_minutes(engine):
    from datetime import timedelta

    from sqlmodel import Session

    from app import crud
    from app.core.db import now

    with Session(engine) as s:
        assert crud.subscribe(s, "a@x.dev", "en")  # new: send the link
        assert crud.subscribe(s, "a@x.dev", "en") is None  # again at once: nothing (no e-mail flood)
        sub = s.exec(select(Subscriber)).one()
        sub.created_at = now(timedelta(minutes=11))
        s.add(sub)
        s.commit()
        assert crud.subscribe(s, "a@x.dev", "en")  # the first link may have been lost: send it again
        crud.confirm(s, sub)
        sub.created_at = now(timedelta(days=1))
        s.add(sub)
        s.commit()
        assert crud.subscribe(s, "a@x.dev", "en") is None  # confirmed: nothing


def test_a_double_submit_saves_one_address(engine, monkeypatch):
    from sqlmodel import Session

    from app import crud

    class NotSavedYet:  # what the second request saw: the address wasn't there when it looked
        def first(self):
            return None

    with Session(engine) as first, Session(engine) as second:
        monkeypatch.setattr(second, "exec", lambda _query: (crud.subscribe(first, "a@x.dev", "en"), NotSavedYet())[1])
        assert crud.subscribe(second, "a@x.dev", "en") is None  # the unique address stops it; no error page
    with Session(engine) as s:
        assert len(s.exec(select(Subscriber)).all()) == 1


def test_draft_post_images_stay_private_in_production(settings, tmp_path):
    import shutil

    from fastapi.testclient import TestClient
    from PIL import Image

    from app.main import create_app

    root = tmp_path / "content"
    shutil.copytree(settings.content_dir, root)
    folder = root / "posts" / "secret"
    (folder / "assets").mkdir(parents=True)
    (folder / "secret.md").write_text("---\ntitle: Secret\ncreated: 2026-01-01\n---\n\nText.\n", encoding="utf-8")
    Image.new("RGB", (4, 4)).save(folder / "assets" / "x.png")
    dev = TestClient(create_app(settings.model_copy(update={"content_dir": root})), base_url=B_ORIGIN)
    assert dev.get("/media/posts/secret/x.png").status_code == 200  # development shows drafts
    prod = settings.model_copy(update={"content_dir": root, "environment": "production"})
    client = TestClient(create_app(prod), base_url=B_ORIGIN.replace("http", "https"))
    assert client.get("/media/posts/secret/x.png").status_code == 404


def test_newsletter_can_be_turned_off(settings, engine):
    from fastapi.testclient import TestClient

    from app.main import create_app

    off = TestClient(create_app(settings.model_copy(update={"newsletter": False})), base_url=B_ORIGIN)
    assert "/api/subscribe" not in off.get("/").text and "/subscribe" not in off.get("/posts/link-or-button").text
    assert off.get("/subscribe").status_code == 404 and "/subscribe</loc>" not in off.get("/sitemap.xml").text
    assert off.post("/api/subscribe", json={"email": "a@x.dev"}, headers={"Origin": B_ORIGIN}).status_code == 404
    assert off.get("/unsubscribe?id=1&t=x").status_code == 400  # links already sent still answer (here: a bad token)

