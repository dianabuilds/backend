from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

ALGO_ALIASES = {
    "fts": "embedding",
    "semantic": "embedding",
    "embedding": "embedding",
    "vector": "embedding",
    "tags": "tags",
    "tag": "tags",
    "random": "random",
    "mix": "explore",
    "explore": "explore",
    "discover": "explore",
}

ALGO_SOURCES = {
    "tags": ["tags"],
    "random": ["random"],
    "embedding": ["embedding", "fts", "semantic", "vector"],
    "explore": ["explore", "mix", "discover"],
}

DEV_BLOG_TAG = "dev-blog"


def isoformat(dt: Any) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        return isoformat(datetime.fromisoformat(str(dt)))
    except (ValueError, TypeError):
        return None


def normalize_algo_key(algo: str | None) -> str:
    key = (algo or "").strip().lower()
    return ALGO_ALIASES.get(key, key or "tags")


def algo_sources(key: str) -> list[str]:
    normalized = normalize_algo_key(key)
    return ALGO_SOURCES.get(normalized, [normalized])


def coerce_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default
