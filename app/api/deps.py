"""Dependencies shared by the routes of both sites: settings, database, content, page rendering, and the gate every
form post goes through (Submit: strict validation, rate limit per IP in SQLite, Turnstile).

Each site is a FastAPI sub-app (app.main); its state holds `settings`, `engine`, `site` ("portfolio" | "blog") and
`pages`. app.core.security.Guard puts the visitor's `lang` and `client_ip` in request.state before any route runs.
Forms accept JSON (forms.js) or a plain form POST (no JavaScript: answered with a redirect, PRG)."""

import asyncio
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy import Engine
from sqlmodel import Session

from .. import content
from ..core import i18n, security
from ..core.config import Settings
from ..models import Form
from ..utils.web import Page, render


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_engine(request: Request) -> Engine:
    return request.app.state.engine


def get_session(engine: Annotated[Engine, Depends(get_engine)]) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def get_content(settings: Annotated[Settings, Depends(get_settings)]) -> content.Content:
    return content.get(settings, drafts=not settings.production)


SettingsDep = Annotated[Settings, Depends(get_settings)]
EngineDep = Annotated[Engine, Depends(get_engine)]
SessionDep = Annotated[Session, Depends(get_session)]
ContentDep = Annotated[content.Content, Depends(get_content)]


def page(request: Request, status: int = 200, nav: str = "") -> Page:
    """The Page of this request: its path is already canonical (the middleware removed /pt)."""
    return Page(settings=get_settings(request), site=request.app.state.site, lang=request.state.lang,
                path=request.url.path, status=status, nav=nav)


def render_page(request: Request, template: str, status: int = 200, nav: str = "", **context) -> Response:
    """The page, or 304 when the browser (or Cloudflare) already holds this exact HTML: pages are `no-cache`, so every
    visit revalidates and an unchanged page costs no transfer."""
    settings = get_settings(request)
    html = render(template, page(request, status, nav), get_content(settings), **context)
    etag = f'W/"{hashlib.sha256(html.encode()).hexdigest()[:20]}"'
    if status == 200 and etag in request.headers.get("if-none-match", ""):
        return Response(status_code=304, headers={"ETag": etag})
    return HTMLResponse(html, status_code=status, headers={"ETag": etag} if status == 200 else None)


def maintenance(request: Request) -> None:
    """Router dependency: 503 while MAINTENANCE=true (assets and /healthz stay up)."""
    if getattr(request.state, "maintenance", False):
        raise HTTPException(503, "maintenance")


# ---- forms

@dataclass
class Submitted[M: Form]:
    data: M
    json: bool  # answered with JSON (forms.js) or a redirect (plain form POST)


async def _parse[M: Form](request: Request, model: type[M]) -> Submitted[M]:
    kind = request.headers.get("content-type", "").split(";")[0].strip().lower()
    try:
        if kind == "application/json":
            data = json.loads(await request.body() or b"{}")
            if not isinstance(data, dict):
                raise ValueError
            return Submitted(model.model_validate(data), True)
        if kind in ("application/x-www-form-urlencoded", "multipart/form-data"):
            form = await request.form()
            return Submitted(model.model_validate({k: v for k, v in form.items() if isinstance(v, str)}), False)
    except (ValidationError, ValueError):
        raise HTTPException(422, "invalid input") from None  # never echo the input back
    raise HTTPException(415, "unsupported content type")


class Submit[M: Form]:
    """Dependency: the validated form, once it passed the rate limit (`name` counts apart) and Turnstile.
    `form: Annotated[Submitted[ContactIn], Depends(Submit(ContactIn, "contact"))]`"""

    def __init__(self, model: type[M], name: str):
        self.model, self.name = model, name

    async def __call__(self, request: Request, settings: SettingsDep, engine: EngineDep) -> Submitted[M]:
        form = await _parse(request, self.model)
        ip = request.state.client_ip
        key = f"{self.name}:{security.client_key(ip)}"
        if not await asyncio.to_thread(security.db_hit, engine, key, settings.form_limit, settings.form_window_seconds):
            raise HTTPException(429, "too many requests")
        host = settings.site_host(request.app.state.site)
        if not await security.verify(settings.turnstile_secret_key, form.data.turnstile, ip, host):
            raise HTTPException(403, "verification failed")
        return form


def done(request: Request, form: Submitted, redirect: str, status: int = 201) -> Response:
    """The answer to a form: JSON for forms.js, a redirect (PRG) for a plain POST."""
    if form.json:
        return JSONResponse({"ok": True}, status)
    return RedirectResponse(i18n.prefix(request.state.lang) + redirect, 303)
