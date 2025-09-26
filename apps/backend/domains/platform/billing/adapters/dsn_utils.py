from __future__ import annotations

from packages.core.config import sanitize_async_dsn


def normalize_async_dsn(url: str) -> str:
    """Ensure DSN is asyncpg-ready and strip libpq-only params."""
    return sanitize_async_dsn(url)


__all__ = ["normalize_async_dsn"]
