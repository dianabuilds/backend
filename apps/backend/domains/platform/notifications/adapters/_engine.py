from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.db import get_async_engine


def ensure_async_engine(engine: AsyncEngine | str, *, name: str = "notifications") -> AsyncEngine:
    if isinstance(engine, AsyncEngine):
        return engine
    return get_async_engine(name, url=engine, pool_pre_ping=True)


__all__ = ["ensure_async_engine"]
