from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeCommentsRepo,
)
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.comments import MemoryNodeCommentsRepo

logger = logging.getLogger(__name__)

_DATETIME_FMT = 'YYYY-MM-DD""T""HH24:MI:SS""Z""'
_MAX_DEPTH = 5


def _serialize_metadata(metadata: dict[str, Any] | None) -> str:
    payload = metadata or {}
    try:
        return json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError("metadata_invalid") from exc


def _normalize_status(value: str) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        raise ValueError("status_required")
    return normalized


class SQLNodeCommentsRepo(NodeCommentsRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            engine
            if isinstance(engine, AsyncEngine)
            else get_async_engine("node-comments", url=engine)
        )

    async def create(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeCommentDTO:
        async with self._engine.begin() as conn:
            depth = 0
            if parent_comment_id is not None:
                parent_sql = text(
                    """
                    SELECT node_id, depth
                      FROM node_comments
                     WHERE id = :parent_id
                    """
                )
                parent_row = (
                    (
                        await conn.execute(
                            parent_sql, {"parent_id": int(parent_comment_id)}
                        )
                    )
                    .mappings()
                    .first()
                )
                if parent_row is None:
                    raise ValueError("parent_not_found")
                if int(parent_row["node_id"]) != int(node_id):
                    raise ValueError("parent_node_mismatch")
                depth = int(parent_row["depth"]) + 1
                if depth > _MAX_DEPTH:
                    raise ValueError("comment_depth_exceeded")
            insert_sql = text(
                """
                INSERT INTO node_comments(node_id, author_id, parent_comment_id, depth, content, metadata)
                VALUES (:node_id, cast(:author_id as uuid), :parent_id, :depth, :content, CAST(:metadata AS jsonb))
                RETURNING id,
                          node_id,
                          author_id::text AS author_id,
                          parent_comment_id,
                          depth,
                          content,
                          status,
                          metadata,
                          to_char(created_at, :fmt) AS created_at,
                          to_char(updated_at, :fmt) AS updated_at
                """
            )
            row = (
                (
                    await conn.execute(
                        insert_sql,
                        {
                            "node_id": int(node_id),
                            "author_id": str(author_id),
                            "parent_id": parent_comment_id,
                            "depth": depth,
                            "content": content,
                            "metadata": _serialize_metadata(metadata),
                            "fmt": _DATETIME_FMT,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if row is None:  # pragma: no cover - defensive
                raise RuntimeError("comment_create_failed")
            return self._row_to_comment(row)

    async def get(self, comment_id: int) -> NodeCommentDTO | None:
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT id,
                               node_id,
                               author_id::text AS author_id,
                               parent_comment_id,
                               depth,
                               content,
                               status,
                               metadata,
                               to_char(created_at, :fmt) AS created_at,
                               to_char(updated_at, :fmt) AS updated_at
                          FROM node_comments
                         WHERE id = :comment_id
                        """
                        ),
                        {"comment_id": int(comment_id), "fmt": _DATETIME_FMT},
                    )
                )
                .mappings()
                .first()
            )
            return self._row_to_comment(row) if row else None

    async def list_for_node(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]:
        filters = ["node_id = :node_id"]
        params: dict[str, Any] = {
            "node_id": int(node_id),
            "fmt": _DATETIME_FMT,
            "limit": int(limit),
            "offset": int(offset),
        }
        if parent_comment_id is None:
            filters.append("parent_comment_id IS NULL")
        else:
            filters.append("parent_comment_id = :parent_id")
            params["parent_id"] = int(parent_comment_id)
        if not include_deleted:
            filters.append("status NOT IN ('deleted','hidden','blocked')")
        query = text(
            f"""
            SELECT id,
                   node_id,
                   author_id::text AS author_id,
                   parent_comment_id,
                   depth,
                   content,
                   status,
                   metadata,
                   to_char(created_at, :fmt) AS created_at,
                   to_char(updated_at, :fmt) AS updated_at
              FROM node_comments
             WHERE {' AND '.join(filters)}
             ORDER BY created_at ASC
             LIMIT :limit OFFSET :offset
            """
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(query, params)).mappings()
            return [self._row_to_comment(row) for row in rows]

    async def update_status(
        self,
        comment_id: int,
        status: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO:
        normalized = _normalize_status(status)
        async with self._engine.begin() as conn:
            current = (
                await conn.execute(
                    text("SELECT metadata FROM node_comments WHERE id = :id"),
                    {"id": int(comment_id)},
                )
            ).scalar_one_or_none()
            if current is None:
                raise ValueError("comment_not_found")
            meta = dict(current or {})
            meta.setdefault("history", []).append(
                {
                    "status": normalized,
                    "actor_id": actor_id,
                    "reason": reason,
                    "at": datetime.now(UTC).replace(microsecond=0).isoformat(),
                }
            )
            update_sql = text(
                """
                UPDATE node_comments
                   SET status = :status,
                       metadata = CAST(:metadata AS jsonb),
                       updated_at = now()
                 WHERE id = :id
                RETURNING id,
                          node_id,
                          author_id::text AS author_id,
                          parent_comment_id,
                          depth,
                          content,
                          status,
                          metadata,
                          to_char(created_at, :fmt) AS created_at,
                          to_char(updated_at, :fmt) AS updated_at
                """
            )
            row = (
                (
                    await conn.execute(
                        update_sql,
                        {
                            "id": int(comment_id),
                            "status": normalized,
                            "metadata": json.dumps(meta, ensure_ascii=False),
                            "fmt": _DATETIME_FMT,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise ValueError("comment_not_found")
            return self._row_to_comment(row)

    async def soft_delete(
        self,
        comment_id: int,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> bool:
        try:
            await self.update_status(
                comment_id,
                "deleted",
                actor_id=actor_id,
                reason=reason,
            )
            return True
        except ValueError:
            return False

    async def hard_delete(self, comment_id: int) -> bool:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text("DELETE FROM node_comments WHERE id = :id"),
                {"id": int(comment_id)},
            )
            deleted = result.rowcount or 0
            return bool(deleted)

    async def lock_node(
        self,
        node_id: int,
        *,
        locked_by: str | None,
        locked_at: str | None,
        reason: str | None = None,
    ) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    UPDATE nodes
                       SET comments_locked_by = CAST(:locked_by AS uuid),
                           comments_locked_at = CAST(:locked_at AS timestamptz),
                           updated_at = now()
                     WHERE id = :node_id
                    """
                ),
                {
                    "node_id": int(node_id),
                    "locked_by": locked_by,
                    "locked_at": locked_at,
                },
            )

    async def set_comments_disabled(
        self,
        node_id: int,
        *,
        disabled: bool,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    UPDATE nodes
                       SET comments_disabled = :disabled,
                           updated_at = now()
                     WHERE id = :node_id
                    """
                ),
                {"disabled": bool(disabled), "node_id": int(node_id)},
            )

    async def record_ban(
        self,
        node_id: int,
        target_user_id: str,
        *,
        set_by: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO:
        async with self._engine.begin() as conn:
            upsert = text(
                """
                INSERT INTO node_comment_bans(node_id, target_user_id, set_by, reason, created_at)
                VALUES (:node_id, cast(:target as uuid), cast(:set_by as uuid), :reason, now())
                ON CONFLICT (node_id, target_user_id)
                DO UPDATE SET set_by = EXCLUDED.set_by,
                              reason = EXCLUDED.reason,
                              created_at = now()
                RETURNING node_id,
                          target_user_id::text AS target_user_id,
                          set_by::text AS set_by,
                          reason,
                          to_char(created_at, :fmt) AS created_at
                """
            )
            row = (
                (
                    await conn.execute(
                        upsert,
                        {
                            "node_id": int(node_id),
                            "target": str(target_user_id),
                            "set_by": str(set_by),
                            "reason": reason,
                            "fmt": _DATETIME_FMT,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if row is None:  # pragma: no cover - defensive
                raise RuntimeError("comment_ban_failed")
            return self._row_to_ban(row)

    async def remove_ban(self, node_id: int, target_user_id: str) -> bool:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(
                    "DELETE FROM node_comment_bans WHERE node_id = :node_id AND target_user_id = cast(:target as uuid)"
                ),
                {"node_id": int(node_id), "target": str(target_user_id)},
            )
            return bool(result.rowcount or 0)

    async def is_banned(self, node_id: int, target_user_id: str) -> bool:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT 1
                      FROM node_comment_bans
                     WHERE node_id = :node_id
                       AND target_user_id = cast(:target as uuid)
                     LIMIT 1
                    """
                ),
                {"node_id": int(node_id), "target": str(target_user_id)},
            )
            return result.scalar_one_or_none() is not None

    async def list_bans(self, node_id: int) -> list[NodeCommentBanDTO]:
        async with self._engine.begin() as conn:
            rows = (
                await conn.execute(
                    text(
                        """
                        SELECT node_id,
                               target_user_id::text AS target_user_id,
                               set_by::text AS set_by,
                               reason,
                               to_char(created_at, :fmt) AS created_at
                          FROM node_comment_bans
                         WHERE node_id = :node_id
                         ORDER BY created_at DESC
                        """
                    ),
                    {"node_id": int(node_id), "fmt": _DATETIME_FMT},
                )
            ).mappings()
            return [self._row_to_ban(row) for row in rows]

    @staticmethod
    def _row_to_comment(row) -> NodeCommentDTO:
        if row is None:
            raise ValueError("comment_not_found")
        metadata = row.get("metadata") or {}
        if not isinstance(metadata, dict):
            try:
                metadata = dict(metadata)
            except Exception:  # pragma: no cover - defensive
                metadata = {}
        return NodeCommentDTO(
            id=int(row["id"]),
            node_id=int(row["node_id"]),
            author_id=str(row["author_id"]),
            parent_comment_id=(
                int(row["parent_comment_id"])
                if row.get("parent_comment_id") is not None
                else None
            ),
            depth=int(row["depth"]),
            content=str(row["content"]),
            status=str(row["status"]),
            metadata=dict(metadata),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _row_to_ban(row) -> NodeCommentBanDTO:
        return NodeCommentBanDTO(
            node_id=int(row["node_id"]),
            target_user_id=str(row["target_user_id"]),
            set_by=str(row["set_by"]),
            reason=row.get("reason"),
            created_at=str(row["created_at"]),
        )


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "node comments repo: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("node comments repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "node comments repo: using memory backend (%s)", reason)


def create_repo(
    settings, *, memory_repo: MemoryNodeCommentsRepo | None = None
) -> NodeCommentsRepo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return memory_repo or MemoryNodeCommentsRepo()
    try:
        return SQLNodeCommentsRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return memory_repo or MemoryNodeCommentsRepo()


__all__ = [
    "SQLNodeCommentsRepo",
    "create_repo",
]
