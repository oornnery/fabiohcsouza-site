"""The blog's newsletter: new posts by e-mail, double opt-in. Posts go out by hand: `python -m app send-post <slug>`.

    POST /api/subscribe     saves the address and e-mails a confirmation link
    /subscribe/confirm      a button; only the POST confirms (mail scanners open every link with a GET)
    /unsubscribe            a button; the POST deletes the address. Mail clients POST here too (RFC 8058 one-click),
                            so the Origin check skips it: the signed link is the guard (app.core.security)

Answers never tell whether an address is subscribed."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlmodel import Session

from ... import crud
from ...core import security
from ...core.config import Settings
from ...models import SubscribeIn, Subscriber
from ...utils import mail
from ..deps import EngineDep, SettingsDep, Submit, Submitted, done, maintenance, render_page

log = logging.getLogger("app.newsletter")
api = APIRouter(prefix="/api", dependencies=[Depends(maintenance)])
router = APIRouter(dependencies=[Depends(maintenance)])  # the pages the e-mails link to: not in the sitemap


async def send_confirmation(settings: Settings, sub: Subscriber) -> None:
    """After the answer (a background task): a failure is logged, never shown to the visitor."""
    confirm_url = security.link(settings, "/subscribe/confirm", "confirm", sub)
    if not settings.production:
        log.info("subscriber #%s: confirm at %s", sub.id, confirm_url)  # development: no mail server needed to try it
    subject, body = mail.compose("confirm", sub.lang, blog=settings.site_host("blog"), link=confirm_url)
    try:
        await mail.send_email(settings, sub.email, subject, body)
    except mail.ProviderError as e:
        log.error("subscriber #%s: confirmation not sent (%s)", sub.id, e)


@api.post("/subscribe")
def subscribe(request: Request, form: Annotated[Submitted[SubscribeIn], Depends(Submit(SubscribeIn, "subscribe"))],
              settings: SettingsDep, engine: EngineDep, tasks: BackgroundTasks):
    if not form.data.is_bot:
        with Session(engine) as s:
            if sub := crud.subscribe(s, form.data.email, request.state.lang):
                tasks.add_task(send_confirmation, settings, sub)
    return done(request, form, "/subscribe?sent=1")


def _page(request: Request, state: str, status: int = 200, **context):
    return render_page(request, "blog/newsletter.html", status, nav="/subscribe", state=state, **context)


@router.get("/subscribe/confirm")
def confirm_page(request: Request, settings: SettingsDep, engine: EngineDep, id: int = 0, t: str = ""):
    with Session(engine) as s:
        sub = crud.signed_subscriber(s, settings, "confirm", id, t)
    return _page(request, "confirm", id=id, t=t) if sub else _page(request, "invalid", 400)


@router.post("/subscribe/confirm")
def confirm(request: Request, settings: SettingsDep, engine: EngineDep, id: int = 0, t: str = ""):
    with Session(engine) as s:
        if (sub := crud.signed_subscriber(s, settings, "confirm", id, t)) is None:
            return _page(request, "invalid", 400)
        crud.confirm(s, sub)
    return _page(request, "confirmed")


@router.get("/unsubscribe")
def unsubscribe_page(request: Request, settings: SettingsDep, engine: EngineDep, id: int = 0, t: str = ""):
    with Session(engine) as s:
        sub = crud.signed_subscriber(s, settings, "unsubscribe", id, t)
    return _page(request, "unsubscribe", id=id, t=t) if sub else _page(request, "invalid", 400)


@router.post("/unsubscribe")
def unsubscribe(request: Request, settings: SettingsDep, engine: EngineDep, id: int = 0, t: str = ""):
    with Session(engine) as s:
        if (sub := crud.signed_subscriber(s, settings, "unsubscribe", id, t)) is None:
            return _page(request, "invalid", 400)
        crud.unsubscribe(s, sub)
    return _page(request, "unsubscribed")
