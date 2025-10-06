from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.application.ports import (
    NodeReactionDTO,
    NodeReactionsRepo,
)
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.reactions import MemoryNodeReactionsRepo

logger = logging.getLogger(__name__)

_DATETIME_FMT = 'YYYY-MM-DD""T""HH24:MI:SS""Z""'


class SQLNodeReactionsRepo(NodeReactionsRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            engine
            if isinstance(engine, AsyncEngine)
            else get_async_engine("node-reactions", url=engine)
        )

    async def add(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool:
        reaction = (reaction_type or "like").strip().lower() or "like"
        async with self._engine.begin() as conn:
            insert_sql = text(
                """
                INSERT INTO node_reactions(node_id, user_id, reaction_type)
                VALUES (:node_id, cast(:user_id as uuid), :reaction)
                ON CONFLICT DO NOTHING
                RETURNING id
                """
            )
            result = await conn.execute(
                insert_sql,
                {
                    "node_id": int(node_id),
                    "user_id": str(user_id),
                    "reaction": reaction,
                },
            )
            inserted = result.first() is not None
            if inserted and reaction == "like":
                await conn.execute(
                    text(
                        "UPDATE nodes SET reactions_like_count = reactions_like_count + 1 WHERE id = :node_id"
                    ),
                    {"node_id": int(node_id)},
                )
            return inserted

    async def remove(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool:
        reaction = (reaction_type or "like").strip().lower() or "like"
        async with self._engine.begin() as conn:
            delete_sql = text(
                """
                DELETE FROM node_reactions
                 WHERE node_id = :node_id
                   AND user_id = cast(:user_id as uuid)
                   AND reaction_type = :reaction
                RETURNING id
                """
            )
            result = await conn.execute(
                delete_sql,
                {
                    "node_id": int(node_id),
                    "user_id": str(user_id),
                    "reaction": reaction,
                },
            )
            deleted = result.first() is not None
            if deleted and reaction == "like":
                await conn.execute(
                    text(
                        """
                        UPDATE nodes
                           SET reactions_like_count = GREATEST(reactions_like_count - 1, 0)
                         WHERE id = :node_id
                        """
                    ),
                    {"node_id": int(node_id)},
                )
            return deleted

    async def has(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool:
        reaction = (reaction_type or "like").strip().lower() or "like"
        async with self._engine.begin() as conn:
            query = text(
                """
                SELECT 1
                  FROM node_reactions
                 WHERE node_id = :node_id
                   AND user_id = cast(:user_id as uuid)
                   AND reaction_type = :reaction
                LIMIT 1
                """
            )
            result = await conn.execute(
                query,
                {
                    "node_id": int(node_id),
                    "user_id": str(user_id),
                    "reaction": reaction,
                },
            )
            return result.scalar_one_or_none() is not None

    async def counts(self, node_id: int) -> dict[str, int]:
        async with self._engine.begin() as conn:
            query = text(
                """
                SELECT reaction_type, COUNT(*) AS total
                  FROM node_reactions
                 WHERE node_id = :node_id
                 GROUP BY reaction_type
                """
            )
            rows = await conn.execute(query, {"node_id": int(node_id)})
            totals: dict[str, int] = {}
            for reaction, total in rows:
                totals[str(reaction)] = int(total)
            return totals

    async def list_for_node(
        self, node_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[NodeReactionDTO]:
        async with self._engine.begin() as conn:
            query = text(
                """
                SELECT id,
                       node_id,
                       user_id::text AS user_id,
                       reaction_type,
                       to_char(created_at, :fmt) AS created_at
                  FROM node_reactions
                 WHERE node_id = :node_id
                 ORDER BY created_at DESC
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
                        "fmt": _DATETIME_FMT,
                    },
                )
            ).mappings()
            return [
                NodeReactionDTO(
                    id=int(row["id"]),
                    node_id=int(row["node_id"]),
                    user_id=str(row["user_id"]),
                    reaction_type=str(row["reaction_type"]),
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ]


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "node reactions repo: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("node reactions repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "node reactions repo: using memory backend (%s)", reason)


def create_repo(
    settings, *, memory_repo: MemoryNodeReactionsRepo | None = None
) -> NodeReactionsRepo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return memory_repo or MemoryNodeReactionsRepo()
    try:
        return SQLNodeReactionsRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return memory_repo or MemoryNodeReactionsRepo()


__all__ = [
    "SQLNodeReactionsRepo",
    "create_repo",
]
