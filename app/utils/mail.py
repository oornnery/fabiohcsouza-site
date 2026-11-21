"""Sending e-mail over SMTP (the standard library, no SDK).

send_email raises ProviderError when the server refuses or can't be reached, and returns quietly when SMTP_HOST is
empty (development). Messages carry personal data: they are never logged.

There is no queue here: the mail server (on the same machine) keeps its own and retries the delivery. If it is down
at the moment of a contact, the message is still in the database (`python -m app leads`) and the log says so."""

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..core import i18n
from ..core.config import APP, Settings

log = logging.getLogger("app.mail")


TEMPLATES = Environment(loader=FileSystemLoader(APP / "templates" / "email"), autoescape=False,  # noqa: S701 — plain-text e-mail, never HTML  # nosec B701
                        undefined=StrictUndefined, keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)
i18n.install(TEMPLATES)


def compose(name: str, lang: str = "en", **context) -> tuple[str, str]:  # noqa: ANN003
    """(subject, body) from templates/email/<name>.txt, in `lang`."""
    with i18n.use(lang):
        head, _, body = TEMPLATES.get_template(f"{name}.txt").render(**context).partition("\n\n")
    return head.removeprefix("Subject: ").strip(), body


class ProviderError(Exception):
    """The mail server refused or can't be reached. The message never includes addresses or the body."""


def _deliver(settings: Settings, message: EmailMessage) -> None:
    tls = ssl.create_default_context()
    if settings.smtp_port == 465:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15, context=tls)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
    with server:
        if settings.smtp_port != 465:
            server.starttls(context=tls)  # never sends the password or a message in the clear
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)


async def send_email(settings: Settings, to: str, subject: str, text: str, *, reply_to: str | None = None,
                     headers: dict[str, str] | None = None) -> None:
    if not settings.mail_provider:
        log.info("e-mail skipped (no SMTP_HOST): %s", subject)
        return
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = settings.email_from, to, subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=parseaddr(settings.email_from)[1].rpartition("@")[2] or None)
    for name, value in (({"Reply-To": reply_to} if reply_to else {}) | (headers or {})).items():
        message[name] = value
    message.set_content(text)
    try:
        await asyncio.to_thread(_deliver, settings, message)
    except (smtplib.SMTPException, OSError) as e:
        raise ProviderError(f"smtp failed: {type(e).__name__}") from None


async def notify_owner(settings: Settings, ref: str, subject: str, text: str, reply_to: str) -> None:
    """Runs after the response (a background task): a failure is logged, never shown to the visitor."""
    try:
        await send_email(settings, settings.owner_email, subject, text, reply_to=reply_to)
    except ProviderError as e:
        log.error("%s is saved but its e-mail was not sent (%s): read it with `python -m app leads`", ref, e)
