"""The ASGI app: the sites in SITE (one per container in production; both in development), picked by the Host header.

    Guard (app.core.security) → Host routing → portfolio sub-app | blog sub-app
                                                ├─ /assets  static/assets, shared by both
                                                └─ the site's routers (app.api.main)

Background: the daily data retention purge (app.crud.purge).
Run: `python -m app serve`, or `uvicorn app.main:create_app --factory`."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Engine
from starlette.routing import Host

from . import content, crud
from .api import errors
from .api.main import PAGES, SITES
from .core.config import STATIC, Settings, get_settings
from .core.db import make_engine
from .core.security import Guard
from .utils import mail
from .utils.web import templates

log = logging.getLogger("app")
DAY = 24 * 3600
health = APIRouter()


@health.get("/healthz", include_in_schema=False)
def healthz():
    return PlainTextResponse("ok")


async def daily_purge(engine: Engine, sites: tuple[str, ...]) -> None:
    while True:
        try:
            log.info("retention: %d rows removed", await asyncio.to_thread(crud.purge, engine, sites))
        except Exception:
            log.exception("retention purge failed")
        await asyncio.sleep(DAY)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    task = asyncio.create_task(daily_purge(app.state.engine, app.state.settings.sites))
    yield
    task.cancel()


def site_app(name: str, settings: Settings, engine: Engine) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, exception_handlers=errors.HANDLERS)
    app.state.settings, app.state.engine, app.state.site, app.state.pages = settings, engine, name, PAGES[name]
    app.mount("/assets", StaticFiles(directory=STATIC / "assets", follow_symlink=False), name="assets")
    for router in SITES[name]:
        app.include_router(router)
    return app


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    engine = make_engine(settings.database_url)
    content.get(settings, drafts=not settings.production)  # fail at start on broken content, not on the first visit
    templates.auto_reload = mail.TEMPLATES.auto_reload = not settings.production  # production: no stat per template

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.settings, app.state.engine = settings, engine
    app.include_router(health)
    for name in settings.sites:
        app.router.routes.append(Host(settings.site_host(name), app=site_app(name, settings, engine)))
    app.add_middleware(Guard, settings=settings)  # runs before the Host routing
    return app
