"""What both sites share: error pages, assets and caching, dates, e-mail over SMTP, analytics."""

import re


def test_404_page_has_status_led_and_noindex(portfolio):
    r = portfolio.get("/does-not-exist")
    assert r.status_code == 404
    assert 'data-status="404"' in r.text and 'content="noindex"' in r.text and "Page not found." in r.text


def test_security_txt(portfolio):
    r = portfolio.get("/.well-known/security.txt")
    assert r.status_code == 200 and "Contact: mailto:" in r.text and "Expires: " in r.text


def test_dates_and_months_come_from_babel(settings):
    import datetime as dt

    from app.core.i18n import js_dict
    from app.utils.web import Page

    en, pt = Page(settings=settings, site="blog"), Page(settings=settings, site="blog", lang="pt")
    d = dt.date(2026, 9, 8)
    assert [en.date(d), pt.date(d), en.date(d, year=False)] == ["Sep 8, 2026", "8 de set. de 2026", "Sep 8"]
    assert [en.month(9), pt.month(9), pt.month(2, full=True)] == ["Sep", "Set", "Fevereiro"]
    assert js_dict("en") == "{}" and "Sep" not in js_dict("pt")


def test_every_css_and_js_file_is_loaded(portfolio):
    """head.html lists the CSS/JS by hand (CSS order matters): a file added or removed must be listed or unlisted."""
    from app.core.config import STATIC

    html = portfolio.get("/").text
    for kind in ("css", "js"):
        loaded = set(re.findall(rf'/assets/{kind}/([\w-]+)\.{kind}', html))
        assert loaded == {f.stem for f in (STATIC / "assets" / kind).glob(f"*.{kind}")}, kind


def test_pages_revalidate_with_an_etag(portfolio):
    r = portfolio.get("/projects")
    assert r.headers["cache-control"] == "no-cache"
    again = portfolio.get("/projects", headers={"If-None-Match": r.headers["etag"]})
    assert again.status_code == 304 and not again.content
    assert portfolio.get("/og.png").headers["cache-control"] == "public, max-age=86400"
    assert "immutable" in portfolio.get("/assets/fonts/geist-wght-normal.woff2").headers["cache-control"]


def test_touch_icon_for_ios(portfolio):
    assert 'rel="apple-touch-icon" href="/apple-touch-icon.png"' in portfolio.get("/").text
    assert portfolio.get("/apple-touch-icon.png").headers["content-type"] == "image/png"


def test_post_images_get_size_and_webp(tmp_path, monkeypatch):
    from PIL import Image

    from app.utils import markdown

    monkeypatch.setattr(markdown, "STATIC", tmp_path)
    (tmp_path / "assets").mkdir()
    Image.new("RGB", (40, 20)).save(tmp_path / "assets" / "shot.png")
    html = markdown.render("![x](/assets/shot.png)").html
    assert 'src="/assets/shot.png" alt="x" loading="lazy" decoding="async" width="40" height="20"' in html
    Image.new("RGB", (40, 20)).save(tmp_path / "assets" / "shot.webp")
    assert 'src="/assets/shot.webp"' in markdown.render("![x](/assets/shot.png)").html
    assert "width" not in markdown.render("![x](/assets/../../etc/passwd)").html  # nothing outside static/ is opened


def test_analytics_only_with_a_token(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    r = TestClient(create_app(settings.model_copy(update={"cf_analytics_token": "abc123"})), base_url="http://portfolio.localhost:8000").get("/")
    assert "static.cloudflareinsights.com/beacon.min.js" in r.text and "cloudflareinsights.com" in r.headers["content-security-policy"]


async def test_smtp_message(settings, monkeypatch):
    import smtplib

    import pytest

    from app.utils import mail

    seen = {}

    class Server:
        def __init__(self, host, port, timeout):
            seen["server"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def starttls(self, context):
            seen["tls"] = True

        def login(self, user, password):
            seen["login"] = (user, password)

        def send_message(self, message):
            seen["message"] = message

    monkeypatch.setattr(smtplib, "SMTP", Server)
    smtp = settings.model_copy(update={"smtp_host": "mail.x.dev", "smtp_user": "site", "smtp_password": "pw",  # noqa: S106
                                       "email_from": "Fabio Souza <contato@x.dev>"})
    await mail.send_email(smtp, "a@b.dev", "Hi", "text", reply_to="r@b.dev", headers={"List-Unsubscribe": "<https://x>"})
    m = seen["message"]
    assert seen["server"] == ("mail.x.dev", 587) and seen["tls"] and seen["login"] == ("site", "pw")  # TLS before the password
    assert (m["From"], m["To"], m["Reply-To"], m["List-Unsubscribe"]) == ("Fabio Souza <contato@x.dev>", "a@b.dev", "r@b.dev", "<https://x>")
    assert m["Message-ID"].endswith("@x.dev>") and m.get_content().strip() == "text"

    def refuse(*_):
        raise smtplib.SMTPRecipientsRefused({})

    monkeypatch.setattr(Server, "send_message", refuse)
    with pytest.raises(mail.ProviderError, match="smtp failed"):
        await mail.send_email(smtp, "a@b.dev", "Hi", "text")
