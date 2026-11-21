import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import Settings
from app.utils import markdown

from .conftest import B_ORIGIN, P_ORIGIN, make_settings

GOOD = {"subject": "Hello there", "name": "Ana", "email": "ana@example.com", "message": "I have a project for you."}


def test_security_headers(portfolio):
    h = portfolio.get("/").headers
    csp = h["content-security-policy"]
    assert "script-src 'self'" in csp and "'unsafe-inline'" not in csp and "frame-ancestors 'none'" in csp
    assert "frame-src 'none'" in csp and "object-src 'none'" in csp and "base-uri 'none'" in csp
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "strict-origin-when-cross-origin" and "camera=()" in h["permissions-policy"]
    assert "server" not in {k.lower() for k in h}


def test_no_inline_scripts_or_styles(portfolio, blog):
    for client, path in ((portfolio, "/"), (portfolio, "/contact"), (blog, "/"), (blog, "/posts/link-or-button")):
        html = client.get(path).text
        assert " style=" not in html and " onclick=" not in html and " onsubmit=" not in html
        for tag in __import__("re").findall(r"<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>", html):
            pytest.fail(f"inline script on {path}: {tag}")


def test_unknown_host_is_refused(app):
    r = TestClient(app, base_url="http://evil.example").get("/")
    assert r.status_code == 421 and r.headers["x-robots-tag"] == "noindex, nofollow"


def test_www_redirects(app):
    r = TestClient(app, base_url="http://www.portfolio.localhost:8000").get("/projects?x=1", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == P_ORIGIN + "/projects?x=1"


@pytest.mark.parametrize("headers", [{}, {"Origin": "https://evil.example"}, {"Origin": B_ORIGIN},
                                     {"Origin": P_ORIGIN, "Sec-Fetch-Site": "cross-site"}])
def test_csrf_origin_check(portfolio, headers):
    assert portfolio.post("/api/contact", json=GOOD, headers=headers).status_code == 403


def test_body_size_cap(portfolio):
    r = portfolio.post("/api/contact", content=b"x" * 40_000, headers={"Origin": P_ORIGIN, "Content-Type": "application/json"})
    assert r.status_code == 413


@pytest.mark.parametrize("field,value", [
    ("subject", "Hi\r\nBcc: victim@example.com"),          # header injection
    ("email", "Ana <victim@example.com>"),                   # display-name smuggling
    ("email", "not-an-email"),
    ("name", "A"),                                            # too short
    ("message", "x" * 6000),                                  # too long
    ("phone", "call me maybe"),
    ("subject", "Hi\x0bBcc: victim@example.com"),           # control characters and Unicode line separators
    ("subject", "Hi\u2028Bcc: victim@example.com"),
    ("subject", "Hi\x1b[31m there"),
    ("name", "Ana\u202egnp.exe"),                             # bidi override
    ("email", "ana\x00@example.com"),
    ("message", "A long enough message\x1b]0;title\x07"),    # terminal escape; tabs and line breaks stay allowed
])
def test_contact_validation(portfolio, field, value):
    r = portfolio.post("/api/contact", json={**GOOD, field: value}, headers={"Origin": P_ORIGIN})
    assert r.status_code == 422
    assert value not in r.text  # never echoes the input back


def test_rate_limit_on_forms(portfolio):
    codes = [portfolio.post("/api/contact", json=GOOD, headers={"Origin": P_ORIGIN}).status_code for _ in range(7)]
    assert codes[:5] == [201] * 5 and codes[5:] == [429, 429]


def test_unsupported_content_type(portfolio):
    r = portfolio.post("/api/contact", content=b"<x/>", headers={"Origin": P_ORIGIN, "Content-Type": "application/xml"})
    assert r.status_code == 415


def test_markdown_is_safe():
    html = markdown.render('<script>alert(1)</script>\n\n[x](javascript:alert(1)) <img src=x onerror=alert(1)>').html
    assert "<script>" not in html and 'href="javascript' not in html and "<img" not in html


def test_asset_path_traversal(portfolio):
    for path in ("/assets/../app/config.py", "/assets/%2e%2e/%2e%2e/pyproject.toml", "/assets/..%2f..%2fpyproject.toml"):
        assert portfolio.get(path).status_code in (400, 404)


def test_insecure_production_config_refused():
    with pytest.raises(ValueError, match="insecure production configuration"):
        Settings(_env_file=None, environment="production", portfolio_url="http://x.dev", blog_url="https://blog.x.dev")
    with pytest.raises(ValueError, match="SMTP_HOST"):  # https, but no e-mail
        Settings(_env_file=None, environment="production", portfolio_url="https://x.dev", blog_url="https://blog.x.dev")


def test_production_config_accepted():
    def prod(**more: str) -> Settings:
        return Settings.model_validate({"environment": "production", "portfolio_url": "https://x.dev", "blog_url": "https://blog.x.dev",
                                        "smtp_host": "mail.x.dev", "email_from": "Me <me@x.dev>", "owner_email": "me@x.dev", **more})

    assert prod(site="portfolio").mail_provider == "smtp"  # the portfolio needs no SECRET_KEY
    with pytest.raises(ValueError, match="SECRET_KEY"):
        prod(site="blog")
    assert prod(secret_key="k" * 32).sites == ("portfolio", "blog")


def test_one_site_per_process(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app(settings.model_copy(update={"site": "portfolio"}))
    assert TestClient(app, base_url=P_ORIGIN).get("/").status_code == 200
    assert TestClient(app, base_url=B_ORIGIN).get("/").status_code == 421  # the blog runs in its own container


def test_api_errors_are_json_and_not_cached(portfolio):
    r = portfolio.post("/api/contact", json={}, headers={"Origin": P_ORIGIN})
    assert r.status_code == 422 and r.json()["detail"] == "invalid input"
    assert r.headers["cache-control"] == "no-store" and r.headers["content-security-policy"].startswith("default-src 'none'")


def test_markdown_tables_have_no_inline_style():
    html = markdown.render("| a | b |\n|:--|--:|\n| 1 | 2 |\n").html
    assert "style=" not in html and 'class="ta-right"' in html


def test_error_page_links_stay_on_this_site(portfolio, blog):
    """/pt//evil.example is a 404 whose language link would be href="//evil.example": another site."""
    for path in ("/pt//evil.example", "//evil.example/x", "/pt///evil.example"):
        html = portfolio.get(path).text
        assert 'href="//' not in html and 'action="//' not in html, path


def test_hostile_values_are_escaped(blog):
    evil = '"><svg/onload=1>'
    for path in ("/tags/" + evil, "/posts/" + evil, "/?q=" + evil):
        assert evil not in blog.get(path).text


def test_malformed_bodies_never_crash(portfolio):
    headers = {"Origin": P_ORIGIN, "Content-Type": "application/json"}
    for body in (b"[" * 15000, b'{"a":' * 5000, b'{"a":"\xff"}', b"null", b'{"email": 1e999}', b""):
        assert portfolio.post("/api/contact", content=body, headers=headers).status_code in (422, 429)


@pytest.mark.parametrize("token,answer,status", [
    ("", None, 403),                                                        # no token: Cloudflare is not even asked
    ("tok", {"success": False}, 403),                                       # Cloudflare says it is a bot
    ("tok", {"success": True, "hostname": "evil.example"}, 403),            # a token solved on another site
    ("tok", {"success": True, "hostname": "portfolio.localhost"}, 201),
    ("tok", "down", 403),                                                   # Cloudflare unreachable: fail closed
])
def test_turnstile(tmp_path, monkeypatch, token, answer, status):
    import httpx

    from app.core import security as turnstile
    from app.main import create_app
    from app.models import Lead

    def cloudflare(request):
        if answer == "down":
            raise httpx.ConnectError("down")
        return httpx.Response(200, json=answer)

    real = httpx.AsyncClient
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(cloudflare), **kw))
    app = create_app(make_settings(database_url=f"sqlite:///{tmp_path / 't.sqlite'}",
                              turnstile_site_key="site", turnstile_secret_key="test-only"))  # noqa: S106
    r = TestClient(app, base_url=P_ORIGIN).post("/api/contact", json={**GOOD, "turnstile": token}, headers={"Origin": P_ORIGIN})
    assert r.status_code == status
    with Session(app.state.engine) as s:
        assert len(s.exec(select(Lead)).all()) == (status == 201)


def test_maintenance_blocks_pages_and_forms(tmp_path):
    from app.main import create_app

    app = create_app(make_settings(database_url=f"sqlite:///{tmp_path / 'm.sqlite'}", maintenance=True))
    c = TestClient(app, base_url=P_ORIGIN)
    assert c.get("/contact").status_code == 503
    assert c.post("/api/contact", json=GOOD, headers={"Origin": P_ORIGIN}).status_code == 503
    assert c.get("/healthz").status_code == 200
