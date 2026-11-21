"""Security at the entry, and the secrets the app checks:

- Guard: the ASGI middleware every request goes through, before any route. Host check (only the configured sites;
  www. redirects), the /pt language prefix, a global rate limit per IP and a body size cap, CSRF for writes (Origin
  must be the site's own and Sec-Fetch-Site same-origin; except the newsletter's one-click unsubscribe, which carries
  its own signed link), maintenance mode, and the security headers on every answer (CSP, HSTS in production, nosniff…).
- Rate limits: MemoryLimiter (per process, every request) and db_hit (SQLite, per form, shared by processes).
  Keys are client IPs, IPv6 grouped by /64.
- Turnstile: Cloudflare's anti-bot check on the forms. Off when TURNSTILE_SECRET_KEY is empty; refused (fail closed)
  when Cloudflare can't be reached.
- Newsletter links: HMAC over purpose, id and address with SECRET_KEY; they stop working once the address is gone."""

import hashlib
import hmac
import ipaddress
import logging
import threading
import time
from collections import deque
from typing import TYPE_CHECKING

import httpx
from sqlalchemy import Engine, text
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from . import i18n
from .config import Settings

if TYPE_CHECKING:
    from ..models import Subscriber

log = logging.getLogger("app.security")


# ---- rate limits

HIT = text(
    """
    INSERT INTO rate_limit (key, hits, window_end) VALUES (:key, 1, :end)
    ON CONFLICT (key) DO UPDATE SET
        hits = CASE WHEN window_end > :now THEN hits + 1 ELSE 1 END,
        window_end = CASE WHEN window_end > :now THEN window_end ELSE :end END
    RETURNING hits
    """
)


def client_key(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip[:64]
    return str(ipaddress.ip_network(f"{addr}/64", strict=False)) if addr.version == 6 else str(addr)


class MemoryLimiter:
    def __init__(self, limit: int, window: float = 60.0, max_keys: int = 50_000):
        self.limit, self.window, self.max_keys = limit, window, max_keys
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > self.max_keys:  # memory bound under a flood of distinct IPs
                self._hits.clear()
            q = self._hits.setdefault(key, deque())
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


def db_hit(engine: Engine, key: str, limit: int, window: float) -> bool:
    """Counts one event; True while `key` is within `limit` per `window` seconds (one atomic statement)."""
    now = time.time()
    with engine.begin() as conn:
        return conn.execute(HIT, {"key": key, "now": now, "end": now + window}).scalar_one() <= limit


# ---- Cloudflare Turnstile

VERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify(secret: str, token: str, ip: str, hostname: str) -> bool:
    if not secret:
        return True
    if not token:
        return False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.post(VERIFY, data={"secret": secret, "response": token, "remoteip": ip})
            result = res.json()
    except (httpx.HTTPError, ValueError):
        log.warning("turnstile unreachable, refusing")
        return False
    return bool(result.get("success")) and result.get("hostname") == hostname


# ---- newsletter links

def token(settings: Settings, purpose: str, sub: Subscriber) -> str:
    message = f"{purpose}:{sub.id}:{sub.email}".encode()
    return hmac.new(settings.secret_key.encode(), message, hashlib.sha256).hexdigest()[:32]


def link(settings: Settings, path: str, purpose: str, sub: Subscriber) -> str:
    return f"{settings.blog_url}{i18n.prefix(sub.lang)}{path}?id={sub.id}&t={token(settings, purpose, sub)}"


# ---- the middleware

MAX_BODY = 32 * 1024  # the largest form is a few KB; fields are capped in app.models
SAFE = ("GET", "HEAD", "OPTIONS")
API_CSP = "default-src 'none'; frame-ancestors 'none'"
XML_CSP = "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'"  # the browser's XML viewer styles itself inline


def csp(settings: Settings) -> str:
    turnstile = " https://challenges.cloudflare.com" if settings.turnstile_site_key else ""
    beacon = bool(settings.cf_analytics_token)  # Cloudflare Web Analytics: its script, and where it reports to
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self'{turnstile}{' https://static.cloudflareinsights.com' if beacon else ''}",  # no inline script anywhere
        "style-src 'self'",
        "font-src 'self'",                          # fonts are self-hosted (assets/fonts)
        "img-src 'self' data:",
        f"connect-src 'self'{' https://cloudflareinsights.com' if beacon else ''}",
        f"frame-src {'https://challenges.cloudflare.com' if turnstile else "'none'"}",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "base-uri 'none'",
        "object-src 'none'",
        "manifest-src 'self'",
        *(["upgrade-insecure-requests"] if settings.production else []),
    ])  # fmt: skip


def client_ip(scope: Scope, settings: Settings) -> str:
    if settings.client_ip_header:
        value = Headers(scope=scope).get(settings.client_ip_header, "")
        if value:
            return value.split(",")[0].strip()[:64]
    return (scope.get("client") or ("0.0.0.0", 0))[0]  # noqa: S104 — fallback client address, not a bind  # nosec B104


class Guard:
    def __init__(self, app: ASGIApp, settings: Settings):
        self.app, self.settings = app, settings
        self.csp = csp(settings)
        self.pages = MemoryLimiter(settings.page_limit_per_minute, 60)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        s = self.settings
        headers = Headers(scope=scope)
        host = headers.get("host", "")
        site = s.site_for_host(host)
        path: str = scope["path"]
        api = path.startswith("/api/")
        is_asset = path.startswith("/assets/")

        def stamped(out: Send) -> Send:
            async def wrapped(message: Message) -> None:
                if message["type"] == "http.response.start":
                    h = MutableHeaders(scope=message)
                    h["X-Content-Type-Options"] = "nosniff"
                    h["Referrer-Policy"] = "strict-origin-when-cross-origin"
                    h["X-Frame-Options"] = "DENY"
                    h["Cross-Origin-Opener-Policy"] = "same-origin"
                    h["Cross-Origin-Resource-Policy"] = "same-site"
                    h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
                    h["Content-Security-Policy"] = API_CSP if api else XML_CSP if path.endswith(".xml") else self.csp
                    if is_asset:
                        # fonts are requested by fonts.css without ?v=: a changed font gets a new file name
                        versioned = b"v=" in scope.get("query_string", b"") or path.startswith("/assets/fonts/")
                        h["Cache-Control"] = "public, max-age=31536000, immutable" if versioned else "public, max-age=3600"
                    elif api:
                        h["Cache-Control"] = "no-store"
                    else:
                        h.setdefault("Cache-Control", "no-cache")
                    if site is None:
                        h["X-Robots-Tag"] = "noindex, nofollow"
                    if s.production:
                        h["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
                await out(message)

            return wrapped

        out = stamped(send)

        def reject(status: int, detail: str):
            return JSONResponse({"detail": detail}, status) if api else PlainTextResponse(detail, status)

        # 1. host
        if site is None:
            bare = host[4:] if host.lower().startswith("www.") else ""
            target = s.site_for_host(bare) if bare else None
            if target:
                qs = scope.get("query_string", b"").decode("latin-1")
                url = s.site_url(target) + path + (f"?{qs}" if qs else "")
                return await RedirectResponse(url, 301)(scope, receive, out)
            if path != "/healthz":
                return await reject(421, "unknown host")(scope, receive, out)

        state = scope.setdefault("state", {})
        state["site"] = site
        ip = client_ip(scope, s)
        state["client_ip"] = ip

        # 2. language prefix
        lang = i18n.LANGS[0]
        for other in i18n.LANGS[1:]:
            prefix = f"/{other}"
            if path == prefix or path.startswith(prefix + "/"):
                lang, path = other, path[len(prefix):] or "/"
                scope = {**scope, "path": path, "raw_path": path.encode()}
        state["lang"] = lang

        if path != "/healthz":
            # 3. rate limit + body size
            if not is_asset and not self.pages.hit(client_key(ip)):
                return await reject(429, "too many requests")(scope, receive, out)
            try:
                length = int(headers.get("content-length") or 0)
            except ValueError:
                return await reject(400, "bad content-length")(scope, receive, out)
            if length > MAX_BODY:
                return await reject(413, "body too large")(scope, receive, out)
            # 4. CSRF (one-click unsubscribe is POSTed by mail clients, from no origin: its signed link is the guard)
            if scope["method"] not in SAFE and not (site == "blog" and path == "/unsubscribe"):
                origin_ok = site is not None and headers.get("origin") == s.site_url(site)
                if not origin_ok or headers.get("sec-fetch-site", "same-origin") != "same-origin":
                    return await reject(403, "forbidden origin")(scope, receive, out)
            # 5. maintenance
            if s.maintenance and not is_asset:
                state["maintenance"] = True

        received = 0

        async def capped() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > MAX_BODY:
                    raise HTTPException(413, "body too large")
            return message

        inner = {**scope, "method": "GET"} if scope["method"] == "HEAD" else scope
        await self.app(inner, capped, out)
