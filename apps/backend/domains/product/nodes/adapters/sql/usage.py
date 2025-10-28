from __future__ import annotations

import asyncio
import logging
from collections import Counter
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.tags.adapters.memory.store import TagUsageStore
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.usage import MemoryUsageProjection

logger = logging.getLogger(__name__)


class SQLUsageProjection:
    """Persist tag usage counters directly in Postgres."""

    def __init__(
        self, engine: AsyncEngine | str, *, content_type: str = "node"
    ) -> None:
        self._engine: AsyncEngine = (
            engine
            if isinstance(engine, AsyncEngine)
            else get_async_engine("tags", url=engine)
        )
        self._content_type = content_type

    def apply_diff(
        self, author_id: str, added: Sequence[str], removed: Sequence[str]
    ) -> None:
        aid = (author_id or "").strip()
        added_slugs = [str(s).strip().lower() for s in added if str(s).strip()]
        removed_slugs = [str(s).strip().lower() for s in removed if str(s).strip()]
        if not aid or (not added_slugs and not removed_slugs):
            return

        add_counts = Counter(added_slugs)
        remove_counts = Counter(removed_slugs)

        async def _run() -> None:
            async with self._engine.begin() as conn:
                if add_counts:
                    sql_inc = text(
                        """
                        INSERT INTO tag_usage_counters(author_id, content_type, slug, count)
                        VALUES (cast(:aid as uuid), :ctype, :slug, :delta)
                        ON CONFLICT (author_id, content_type, slug)
                        DO UPDATE SET count = tag_usage_counters.count + EXCLUDED.count
                        """
                    )
                    params = [
                        {
                            "aid": aid,
                            "ctype": self._content_type,
                            "slug": slug,
                            "delta": delta,
                        }
                        for slug, delta in add_counts.items()
                    ]
                    await conn.execute(sql_inc, params)
                if remove_counts:
                    sql_dec = text(
                        """
                        UPDATE tag_usage_counters
                           SET count = GREATEST(count - :delta, 0)
                         WHERE author_id = cast(:aid as uuid)
                           AND content_type = :ctype
                           AND slug = :slug
                        """
                    )
                    dec_params = [
                        {
                            "aid": aid,
                            "ctype": self._content_type,
                            "slug": slug,
                            "delta": delta,
                        }
                        for slug, delta in remove_counts.items()
                    ]
                    await conn.execute(sql_dec, dec_params)
                    sql_del = text(
                        """
                        DELETE FROM tag_usage_counters
                         WHERE author_id = cast(:aid as uuid)
                           AND content_type = :ctype
                           AND slug = ANY(:slugs)
                           AND count <= 0
                        """
                    )
                    await conn.execute(
                        sql_del,
                        {
                            "aid": aid,
                            "ctype": self._content_type,
                            "slugs": list(remove_counts.keys()),
                        },
                    )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.create_task(_run())


__all__ = ["SQLUsageProjection"]


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "node usage projection: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("node usage projection: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "node usage projection: using memory backend (%s)", reason)


def create_projection(
    settings,
    *,
    store: TagUsageStore | None = None,
    content_type: str = "node",
) -> MemoryUsageProjection | SQLUsageProjection:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return MemoryUsageProjection(
            store or TagUsageStore(), content_type=content_type
        )
    try:
        return SQLUsageProjection(decision.dsn, content_type=content_type)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return MemoryUsageProjection(
            store or TagUsageStore(), content_type=content_type
        )


__all__ = [
    "SQLUsageProjection",
    "create_projection",
]
