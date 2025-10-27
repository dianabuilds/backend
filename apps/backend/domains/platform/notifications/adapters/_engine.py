from __future__ import annotations

from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import NullPool

from packages.core.db import get_async_engine


def ensure_async_engine(
    engine: AsyncEngine | str | Any, *, name: str = "notifications"
) -> AsyncEngine:
    if isinstance(engine, AsyncEngine):
        return engine
    if hasattr(engine, "begin") and callable(engine.begin):
        return cast(AsyncEngine, engine)
    return get_async_engine(
        f"{name}.repo",
        url=engine,
        cache=False,
        pool_pre_ping=False,
        poolclass=NullPool,
    )


__all__ = ["ensure_async_engine"]
