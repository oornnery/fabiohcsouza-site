"""SQLite engine. WAL mode so readers never block the writer; foreign keys and a busy timeout on every connection."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine, event
from sqlmodel import SQLModel, create_engine


def now(ago: timedelta = timedelta()) -> str:
    """UTC timestamp, ISO 8601 (sorts like a date); `ago` moves it back (the retention cutoff)."""
    return (datetime.now(UTC) - ago).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_engine(url: str) -> Engine:
    if url.startswith("sqlite:///") and ":memory:" not in url:
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 10})

    @event.listens_for(engine, "connect")
    def _pragmas(conn, _record):  # noqa: ANN001
        for pragma in ("journal_mode=WAL", "synchronous=NORMAL", "foreign_keys=ON"):
            conn.execute(f"PRAGMA {pragma}")

    SQLModel.metadata.create_all(engine)  # the tables of every model module imported so far (app.main imports the sites)
    return engine
