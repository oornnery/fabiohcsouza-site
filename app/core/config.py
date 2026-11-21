"""Settings from environment variables (and .env in development). Documented in .env.example.

Production refuses to start with an insecure configuration instead of running half-protected."""

import re
from functools import cached_property
from pathlib import Path
from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
STATIC = APP / "static"  # CSS, JS, fonts and images, served at /assets on both sites
SITES = ("portfolio", "blog")
DOMAINS = {"portfolio": "fabiohcsouza.dev", "blog": "blog.fabiohcsouza.dev"}  # the public names (wordmark, share images, signature)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_ignore_empty=True, extra="ignore")

    environment: Literal["development", "production"] = "development"
    # The site this process serves: one container per site in production (docker/compose.yml). Empty: both (development).
    site: Literal["", "portfolio", "blog"] = ""
    # The blog is live: the portfolio links to it (menu, footer, latest posts on the home, RSS, a work's post).
    # Off until there is something to read; the blog's own pages always link to themselves.
    blog: bool = False
    # The blog's newsletter: the subscribe form, /subscribe and POST /api/subscribe. Off: they're hidden and answer 404;
    # the confirm and unsubscribe links in e-mails already sent keep working.
    newsletter: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    maintenance: bool = False  # every page answers 503 (health check still works)

    database_url: str = f"sqlite:///{ROOT / '.local' / 'app.sqlite'}"
    content_dir: Path = ROOT / "content"

    # Public origin of each site. One process serves both and picks the site by Host. Writes must come from the
    # same origin (CSRF). In development *.localhost resolves to this machine without any setup.
    portfolio_url: str = "http://portfolio.localhost:8000"
    blog_url: str = "http://blog.localhost:8000"

    # Header with the visitor IP set by the proxy in front (Cloudflare: cf-connecting-ip). Empty = socket address.
    # Only trust it when nothing reaches the app except through that proxy.
    client_ip_header: str = ""

    # E-mail over SMTP (the mail server's submission port). No host = e-mails are only logged (development, tests).
    # Production refuses to start without one: the contact form depends on it.
    smtp_host: str = ""
    smtp_port: int = 587  # 587 = STARTTLS, 465 = TLS from the first byte
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""  # "Fabio Souza <contact@fabiohcsouza.dev>" (an address the SMTP user may send as)
    owner_email: str = ""  # where contact messages go

    # Signs the newsletter's confirm and unsubscribe links (HMAC). Production refuses to start the blog without one:
    # `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Changing it breaks the links already sent.
    secret_key: str = ""

    # Optional Cloudflare Turnstile on forms. Empty = skipped (honeypot + rate limits still apply).
    turnstile_site_key: str = ""
    turnstile_secret_key: str = ""

    # Optional Cloudflare Web Analytics (no cookies, no consent banner): the site token of dash > Web Analytics.
    cf_analytics_token: str = ""

    # Rate limits
    page_limit_per_minute: int = 240  # every request except /assets, per IP (memory)
    form_limit: int = 5  # form posts per IP per window (SQLite, survives restarts)
    form_window_seconds: int = 600

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @property
    def sites(self) -> tuple[str, ...]:
        """The sites this process serves."""
        return (self.site,) if self.site else SITES

    @property
    def mail_provider(self) -> Literal["smtp", ""]:
        return "smtp" if self.smtp_host else ""

    def site_url(self, site: str) -> str:
        return getattr(self, f"{site}_url")

    def site_host(self, site: str) -> str:
        """'blog.fabiohcsouza.dev' (no scheme, no port)."""
        return self.site_url(site).split("://", 1)[1].split(":")[0].lower()

    @cached_property
    def _hosts(self) -> dict[str, str]:
        return {self.site_host(s): s for s in self.sites}

    def site_for_host(self, host: str) -> str | None:
        """'portfolio' | 'blog' for a Host header (port ignored), None if unknown or not served here."""
        return self._hosts.get(host.split(":")[0].lower().rstrip("."))

    @field_validator("portfolio_url", "blog_url")
    @classmethod
    def _origin(cls, value: str) -> str:
        value = value.rstrip("/")
        if not re.fullmatch(r"https?://[a-z0-9.-]+(:\d+)?", value):
            raise ValueError("must be an origin such as https://example.com")
        return value

    @model_validator(mode="after")
    def _safe(self) -> Self:
        if not self.production:
            return self
        problems = [f"{n.upper()} must be https" for n in ("portfolio_url", "blog_url") if not getattr(self, n).startswith("https://")]
        if not self.mail_provider:
            problems.append("set SMTP_HOST: forms send e-mail")
        if bool(self.smtp_user) != bool(self.smtp_password):
            problems.append("SMTP_USER and SMTP_PASSWORD go together")
        if not (self.email_from and self.owner_email):
            problems.append("EMAIL_FROM and OWNER_EMAIL are required")
        if "blog" in self.sites and len(self.secret_key) < 32:
            problems.append("SECRET_KEY must have 32+ characters: it signs the newsletter links")
        if bool(self.turnstile_site_key) != bool(self.turnstile_secret_key):
            problems.append("TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY go together")
        if problems:
            raise ValueError("insecure production configuration: " + "; ".join(problems))
        return self


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
