from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return current UTC time with tzinfo."""
    return datetime.now(UTC)


def isoformat_utc(value: datetime | None) -> str | None:
    """Normalize datetime to ISO-8601 string in UTC with trailing Z."""
    if value is None:
        return None
    dt = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(
    value: Any, *, logger_override: logging.Logger | None = None
) -> datetime | None:
    """Parse arbitrary ISO-like value into aware UTC datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            text = str(value).strip()
            if not text:
                return None
            text = text.replace("Z", "+00:00")
            dt = datetime.fromisoformat(text)
        except (TypeError, ValueError) as exc:
            (logger_override or logger).debug(
                "Failed to parse datetime %r: %s", value, exc
            )
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def paginate(
    seq: Sequence[Any] | Iterable[Any],
    limit: int,
    cursor: str | None,
    *,
    logger_override: logging.Logger | None = None,
    max_limit: int = 200,
    default: int = 50,
) -> tuple[list[Any], str | None]:
    """Return slice of items and next cursor respecting bounds."""
    try:
        limit_value = max(1, min(int(limit or default), max_limit))
    except (TypeError, ValueError):
        limit_value = default
    offset = 0
    if cursor:
        try:
            offset = max(0, int(cursor))
        except (TypeError, ValueError) as exc:
            (logger_override or logger).debug(
                "Invalid pagination cursor %r: %s", cursor, exc
            )
            offset = 0
    items = list(seq)
    chunk = items[offset : offset + limit_value]
    next_cursor = (
        str(offset + limit_value) if offset + limit_value < len(items) else None
    )
    return chunk, next_cursor


def generate_id(prefix: str, *, length: int = 10) -> str:
    """Generate predictable short id with the given prefix."""
    return f"{prefix}_{uuid4().hex[:length]}"


__all__ = [
    "utc_now",
    "isoformat_utc",
    "parse_iso_datetime",
    "paginate",
    "generate_id",
]

IsoConverter = Callable[[datetime | None], str | None]


def resolve_iso(target: object) -> IsoConverter:
    """Return a datetime->iso converter, falling back to isoformat_utc."""
    candidate = getattr(target, "_iso", None)
    if callable(candidate):
        return cast(IsoConverter, candidate)
    return cast(IsoConverter, isoformat_utc)
