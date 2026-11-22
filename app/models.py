"""The database tables and the input of the public forms.

Tables (SQLite; app.core.db creates them): Lead (contact messages), Subscriber and Delivery (newsletter), PostLike
(a count per post), RateLimit (form counters). Personal data is kept to the minimum and deleted on a schedule (app.crud.purge).

Forms: browser checks are UX only, these models are the real boundary. Every field is length-capped; single-line
fields reject every control character, line/paragraph separators and bidi overrides (they end up in e-mail subjects
and headers); the message keeps only tab and line breaks; e-mail addresses reject the characters that would let a
display name smuggle another recipient."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from sqlmodel import Field, SQLModel

from .core.db import now

# ---- tables

class Lead(SQLModel, table=True):
    """A message from the contact form."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: str = Field(default_factory=now, index=True)
    lang: str = "en"
    subject: str
    name: str
    email: str
    phone: str | None = None
    message: str


class Subscriber(SQLModel, table=True):
    """An address that asked for new posts. Only the address, its language and two dates."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    lang: str = "en"
    created_at: str = Field(default_factory=now, index=True)
    confirmed_at: str | None = None


class Delivery(SQLModel, table=True):
    """A post e-mailed to a subscriber: send-post skips it next time (a failed run resumes, nobody gets it twice)."""

    slug: str = Field(primary_key=True)
    subscriber_id: int = Field(primary_key=True, foreign_key="subscriber.id", ondelete="CASCADE")
    sent_at: str = Field(default_factory=now)


class PostLike(SQLModel, table=True):
    """The likes of a post: only the total, nothing about who liked it."""

    __tablename__ = "post_like"
    slug: str = Field(primary_key=True)
    count: int = 0


class RateLimit(SQLModel, table=True):
    """Fixed-window counters for the forms (shared by workers, survive restarts). Keys contain IPs: purged."""

    __tablename__ = "rate_limit"
    key: str = Field(primary_key=True)
    hits: int = 0
    window_end: float = 0


# ---- form input

_CTRL = r"\x00-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069"
_TEXT = r"\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"  # control characters except tab, LF and CR
_PART = rf'[^@\s<>",;:()\[\]\\{_CTRL}]+'
Email = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=254, pattern=rf"^{_PART}@{_PART}\.{_PART}$")]


def line(min_length: int, max_length: int) -> StringConstraints:
    return StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length, pattern=rf"^[^{_CTRL}]*$")


def paragraph(min_length: int, max_length: int) -> StringConstraints:
    return StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length, pattern=rf"^[^{_TEXT}]*$")


class Form(BaseModel):
    """Fields every form carries: the honeypot and the Turnstile token."""

    model_config = ConfigDict(extra="ignore", str_max_length=10_000)
    website: Annotated[str, StringConstraints(max_length=200)] = ""  # honeypot: real people leave it empty
    turnstile: Annotated[str, StringConstraints(max_length=2048)] = ""

    @property
    def is_bot(self) -> bool:
        return bool(self.website.strip())


class ContactIn(Form):
    subject: Annotated[str, line(3, 120)]
    name: Annotated[str, line(2, 80)]
    email: Email
    phone: Annotated[str, line(0, 30)] = ""
    message: Annotated[str, paragraph(10, 5000)]

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        if v and sum(c.isdigit() for c in v) < 8:
            raise ValueError("phone needs 8+ digits")
        if v and not all(c.isdigit() or c in " +()-." for c in v):
            raise ValueError("invalid phone")
        return v


class SubscribeIn(Form):
    email: Email
