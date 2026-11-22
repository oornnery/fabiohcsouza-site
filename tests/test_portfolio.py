"""The portfolio: every page in both languages, and the contact form (saved, then e-mailed; kept 2 years)."""

import pytest
from sqlmodel import Session, select

from app import content
from app.api.routes import portfolio as routes
from app.models import Lead

from .conftest import P_ORIGIN, make_settings

# every registered page (app.api.pages): a new page is tested without touching this file
PAGES = [path for _, path, _ in routes.router.urls(content.get(make_settings()))]
GOOD = {"subject": "Hello there", "name": "Ana", "email": "Ana@Example.com", "message": "I have a project for you."}


@pytest.mark.parametrize("lang", ["", "/pt"])
@pytest.mark.parametrize("path", PAGES)
def test_portfolio_pages(portfolio, path, lang):
    r = portfolio.get(lang + path)
    assert r.status_code == 200
    assert '<html lang="pt-BR"' in r.text if lang else '<html lang="en"' in r.text
    assert 'rel="canonical"' in r.text and 'hreflang="pt-BR"' in r.text


def test_contact_is_saved_then_e_mailed(portfolio, engine, monkeypatch):
    from app.utils import mail

    sent = []

    async def fake(settings, to, subject, text, **kw):
        sent.append((to, subject, kw.get("reply_to")))
        raise mail.ProviderError("smtp failed: test")  # the mail server is down: the visitor still gets 201

    monkeypatch.setattr(mail, "send_email", fake)
    r = portfolio.post("/pt/api/contact", json=GOOD, headers={"Origin": P_ORIGIN})
    assert r.status_code == 201 and r.json() == {"ok": True}
    with Session(engine) as s:
        lead = s.exec(select(Lead)).one()
        assert lead.email == "ana@example.com" and lead.lang == "pt"  # saved whatever happens to the e-mail
    assert sent == [("", "Contact: Hello there", "ana@example.com")]  # owner_email is empty in the tests


def test_contact_without_javascript_redirects(portfolio):
    r = portfolio.post("/pt/api/contact", data=GOOD, headers={"Origin": P_ORIGIN}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/pt/contact?sent=1"
    assert "Mensagem recebida." in portfolio.get("/pt/contact?sent=1").text


def test_honeypot_looks_accepted_but_stores_nothing(portfolio, engine):
    r = portfolio.post("/api/contact", json={**GOOD, "website": "http://spam"}, headers={"Origin": P_ORIGIN})
    assert r.status_code == 201
    with Session(engine) as s:
        assert s.exec(select(Lead)).first() is None


def test_lead_e_mail_is_in_english_for_the_owner():
    from app.utils.mail import compose as email

    subject, body = email("lead", lead=Lead(subject="Hi", name="Ana", email="a@x.dev", message="hello there", lang="pt"))
    assert subject == "Contact: Hi" and "Ana <a@x.dev>" in body
    assert email("lead", "pt", lead=Lead(subject="Hi", name="A", email="a@x.dev", message="m"))[0] == "Contact: Hi"


def test_old_contacts_are_deleted_after_two_years(engine):
    from datetime import timedelta

    from app.core.db import now
    from app.crud import purge

    with Session(engine) as s:
        s.add(Lead(**GOOD, created_at=now(timedelta(days=731))))
        s.add(Lead(**{**GOOD, "subject": "Recent"}, created_at=now(timedelta(days=729))))
        s.commit()
    purge(engine, ("portfolio",))
    with Session(engine) as s:
        assert [lead.subject for lead in s.exec(select(Lead))] == ["Recent"]


def test_robots_and_sitemap(portfolio):
    assert "Sitemap: http://portfolio.localhost:8000/sitemap.xml" in portfolio.get("/robots.txt").text
    sitemap = portfolio.get("/sitemap.xml").text
    assert all(f"{path}</loc>" in sitemap for path in PAGES if path != "/") and "/posts/" not in sitemap


def test_no_blog_links_until_blog_is_on(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    client = TestClient(create_app(settings.model_copy(update={"blog": False})), base_url=P_ORIGIN)
    for path in ("/", "/projects", "/about", "/contact", "/privacy"):
        assert "blog.localhost" not in client.get(path).text, path
    assert "blog.localhost" in TestClient(create_app(settings), base_url=P_ORIGIN).get("/").text  # BLOG=true


def test_projects_newest_first_with_their_own_page(portfolio):
    from app.content.projects import set_updated

    html = portfolio.get("/projects").text
    assert html.index('id="work"') < html.index('id="open-source"')  # Work first
    assert html.index("/projects/sipx") < html.index("/projects/icmpx")  # newer commit first
    page = portfolio.get("/pt/projects/fabiohcsouza")
    assert page.status_code == 200 and "Atualizado em" in page.text and "/media/projects/fabiohcsouza/" in page.text
    assert portfolio.get("/projects/nope").status_code == 404
    text = "---\ntitle: x\nupdated: 2020-01-01\n---\n\nbody\n"
    assert set_updated(text, "2026-11-21") == "---\ntitle: x\nupdated: 2026-11-21\n---\n\nbody\n"
    assert "updated: 2026-11-21\n---\n" in set_updated("---\ntitle: x\n---\n", "2026-11-21")
