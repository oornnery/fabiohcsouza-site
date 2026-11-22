"""Reads and writes of the tables in app.models, shared by the routes and the command line."""

import hmac
import time
from datetime import timedelta

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, delete, func, select

from .core import security
from .core.config import Settings
from .core.db import now
from .models import ContactIn, Delivery, Lead, PostLike, RateLimit, Subscriber

KEEP_LEADS = timedelta(days=730)  # contact messages: 2 years
KEEP_UNCONFIRMED = timedelta(days=7)  # newsletter addresses never confirmed
RESEND_AFTER = timedelta(minutes=10)  # a second subscribe of an unconfirmed address sends the link again after this


LIKE = text("INSERT INTO post_like (slug, count) VALUES (:slug, 1) ON CONFLICT (slug) DO UPDATE SET count = count + 1 RETURNING count")
UNLIKE = text("UPDATE post_like SET count = max(count - 1, 0) WHERE slug = :slug RETURNING count")


# ---- likes

def like(session: Session, slug: str) -> int:
    """One more like (one atomic statement); returns the new total."""
    count = session.connection().execute(LIKE, {"slug": slug}).scalar_one()
    session.commit()
    return count


def unlike(session: Session, slug: str) -> int:
    """One like less, never below zero; returns the new total."""
    count = session.connection().execute(UNLIKE, {"slug": slug}).scalar_one_or_none()
    session.commit()
    return count or 0


def likes(session: Session, slug: str) -> int:
    row = session.get(PostLike, slug)
    return row.count if row else 0


# ---- contact

def save_lead(session: Session, form: ContactIn, lang: str) -> Lead:
    lead = Lead(lang=lang, **form.model_dump(include={"subject", "name", "email", "message"}), phone=form.phone or None)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def latest_leads(session: Session, n: int) -> list[Lead]:
    return list(session.exec(select(Lead).order_by(col(Lead.id).desc()).limit(n)))


def count_leads(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Lead)).one()


# ---- newsletter

def subscribe(session: Session, email: str, lang: str) -> Subscriber | None:
    """The subscriber to e-mail a confirmation link to, or None: already confirmed, asked less than 10 minutes ago,
    or the same address saved by another request at this moment. The visitor gets the same answer either way."""
    sub = session.exec(select(Subscriber).where(Subscriber.email == email)).first()
    if sub and (sub.confirmed_at or sub.created_at > now(RESEND_AFTER)):
        return None
    if sub:  # never confirmed: maybe the first e-mail was lost; the 7 days start again
        sub.created_at = now()
    else:
        sub = Subscriber(email=email, lang=lang)
    session.add(sub)
    try:
        session.commit()
    except IntegrityError:  # a double submit: the other request saved the address and sends its link
        session.rollback()
        return None
    session.refresh(sub)
    return sub


def signed_subscriber(session: Session, settings: Settings, purpose: str, id: int, token: str) -> Subscriber | None:
    """The subscriber a newsletter link points to, if its signature matches."""
    sub = session.get(Subscriber, id) if id > 0 and len(token) == 32 else None
    return sub if sub and hmac.compare_digest(token, security.token(settings, purpose, sub)) else None


def confirm(session: Session, sub: Subscriber) -> None:
    sub.confirmed_at = sub.confirmed_at or now()
    session.add(sub)
    session.commit()


def unsubscribe(session: Session, sub: Subscriber) -> None:
    session.delete(sub)  # its deliveries go with it (ON DELETE CASCADE)
    session.commit()


def subscriber_counts(session: Session) -> tuple[int, int]:
    """(confirmed, unconfirmed)."""
    total = session.exec(select(func.count()).select_from(Subscriber)).one()
    confirmed = session.exec(select(func.count()).select_from(Subscriber).where(col(Subscriber.confirmed_at).is_not(None))).one()
    return confirmed, total - confirmed


def waiting_for(session: Session, slug: str) -> list[Subscriber]:
    """The confirmed subscribers who haven't got this post yet."""
    sent = select(Delivery.subscriber_id).where(Delivery.slug == slug)
    return list(session.exec(select(Subscriber).where(col(Subscriber.confirmed_at).is_not(None), col(Subscriber.id).not_in(sent))))


def record_delivery(session: Session, slug: str, sub: Subscriber) -> None:
    session.add(Delivery(slug=slug, subscriber_id=sub.id or 0))
    session.commit()


# ---- data retention (LGPD): at start, once a day, and with `python -m app purge`

def purge(engine: Engine, sites: tuple[str, ...]) -> int:
    """Old contact messages (portfolio), unconfirmed addresses (blog) and expired rate-limit counters. Returns how
    many rows went."""
    with Session(engine) as s:
        n = 0
        if "portfolio" in sites:
            n += s.exec(delete(Lead).where(col(Lead.created_at) < now(KEEP_LEADS))).rowcount  # type: ignore[call-overload]
        if "blog" in sites:
            old = col(Subscriber.confirmed_at).is_(None) & (col(Subscriber.created_at) < now(KEEP_UNCONFIRMED))
            n += s.exec(delete(Subscriber).where(old)).rowcount  # type: ignore[call-overload]
        n += s.exec(delete(RateLimit).where(col(RateLimit.window_end) <= time.time())).rowcount  # type: ignore[call-overload]
        s.commit()
    return n
