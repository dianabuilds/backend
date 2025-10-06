from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.application.ports import NodeViewsRepo, NodeViewStat
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.views import MemoryNodeViewsRepo

logger = logging.getLogger(__name__)


def _parse_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return datetime.now(UTC)


class SQLNodeViewsRepo(NodeViewsRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            engine
            if isinstance(engine, AsyncEngine)
            else get_async_engine("node-views", url=engine)
        )

    async def increment(
        self,
        node_id: int,
        *,
        amount: int = 1,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        at: str | None = None,
    ) -> int:
        delta = int(amount)
        if delta <= 0:
            raise ValueError("amount_positive_required")
        when = _parse_at(at)
        bucket = when.date()
        async with self._engine.begin() as conn:
            update_node = text(
                """
                UPDATE nodes
                   SET views_count = COALESCE(views_count, 0) + :delta,
                       updated_at = now()
                 WHERE id = :node_id
                RETURNING views_count
                """
            )
            result = await conn.execute(
                update_node, {"delta": delta, "node_id": int(node_id)}
            )
            row = result.first()
            if row is None:
                raise ValueError("node_not_found")
            total = int(row[0])
            upsert_daily = text(
                """
                INSERT INTO node_views_daily(node_id, bucket_date, views, updated_at)
                VALUES (:node_id, CAST(:bucket AS date), :delta, now())
                ON CONFLICT (node_id, bucket_date)
                DO UPDATE SET
                    views = node_views_daily.views + EXCLUDED.views,
                    updated_at = GREATEST(node_views_daily.updated_at, now())
                """
            )
            await conn.execute(
                upsert_daily,
                {"node_id": int(node_id), "bucket": bucket, "delta": delta},
            )
        return total

    async def get_total(self, node_id: int) -> int:
        async with self._engine.begin() as conn:
            query = text("SELECT views_count FROM nodes WHERE id = :node_id")
            result = await conn.execute(query, {"node_id": int(node_id)})
            value = result.scalar_one_or_none()
            return int(value or 0)

    async def get_daily(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]:
        async with self._engine.begin() as conn:
            query = text(
                """
                SELECT bucket_date, views
                  FROM node_views_daily
                 WHERE node_id = :node_id
                 ORDER BY bucket_date DESC
                 LIMIT :limit OFFSET :offset
                """
            )
            rows = (
                await conn.execute(
                    query,
                    {
                        "node_id": int(node_id),
                        "limit": int(limit),
                        "offset": int(offset),
                    },
                )
            ).mappings()
            stats: list[NodeViewStat] = []
            for row in rows:
                bucket_date: date = row["bucket_date"]
                stats.append(
                    NodeViewStat(
                        node_id=int(node_id),
                        bucket_date=bucket_date.isoformat(),
                        views=int(row["views"] or 0),
                    )
                )
            return stats


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "node views repo: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("node views repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "node views repo: using memory backend (%s)", reason)


def create_repo(
    settings, *, memory_repo: MemoryNodeViewsRepo | None = None
) -> NodeViewsRepo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return memory_repo or MemoryNodeViewsRepo()
    try:
        return SQLNodeViewsRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return memory_repo or MemoryNodeViewsRepo()


__all__ = [
    "SQLNodeViewsRepo",
    "create_repo",
]
