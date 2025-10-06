from __future__ import annotations

import builtins
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastCollection,
    BroadcastCreateModel,
    BroadcastStatus,
    BroadcastUpdateModel,
)
from domains.platform.notifications.ports import BroadcastRepo

from .._engine import ensure_async_engine


class SQLBroadcastRepo(BroadcastRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine = ensure_async_engine(engine)

    async def create(self, payload: BroadcastCreateModel) -> Broadcast:
        sql = text(
            """
            INSERT INTO notification_broadcasts (
                title,
                body,
                template_id,
                audience_type,
                audience_filters,
                audience_user_ids,
                status,
                created_by,
                scheduled_at
            ) VALUES (
                :title,
                :body,
                :template_id,
                :audience_type,
                :audience_filters,
                :audience_user_ids,
                :status,
                :created_by,
                :scheduled_at
            )
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        sql,
                        self._prepare_write_params(payload, created=True),
                    )
                )
                .mappings()
                .first()
            )
            assert row is not None
            return self._row_to_model(cast(Mapping[str, Any], row))

    async def update(
        self, broadcast_id: str, payload: BroadcastUpdateModel
    ) -> Broadcast:
        sql = text(
            """
            UPDATE notification_broadcasts
            SET
                title = :title,
                body = :body,
                template_id = :template_id,
                audience_type = :audience_type,
                audience_filters = :audience_filters,
                audience_user_ids = :audience_user_ids,
                status = :status,
                scheduled_at = :scheduled_at,
                updated_at = now()
            WHERE id = :id
            RETURNING *
            """
        )
        params = self._prepare_write_params(payload, created=False)
        params["id"] = broadcast_id
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, params)).mappings().first()
            if row is None:
                raise RuntimeError(f"Broadcast {broadcast_id} not found")
            return self._row_to_model(cast(Mapping[str, Any], row))

    async def update_status(
        self,
        broadcast_id: str,
        *,
        status: BroadcastStatus,
        scheduled_at: datetime | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        total: int | None = None,
        sent: int | None = None,
        failed: int | None = None,
    ) -> Broadcast:
        set_clauses = ["status = :status", "updated_at = now()"]
        params: dict[str, Any] = {"id": broadcast_id, "status": status.value}

        if scheduled_at is not None:
            set_clauses.append("scheduled_at = :scheduled_at")
            params["scheduled_at"] = scheduled_at
        elif status is BroadcastStatus.CANCELLED:
            set_clauses.append("scheduled_at = NULL")

        if started_at is not None:
            set_clauses.append("started_at = :started_at")
            params["started_at"] = started_at

        if finished_at is not None:
            set_clauses.append("finished_at = :finished_at")
            params["finished_at"] = finished_at

        if total is not None:
            set_clauses.append("total = :total")
            params["total"] = total

        if sent is not None:
            set_clauses.append("sent = :sent")
            params["sent"] = sent

        if failed is not None:
            set_clauses.append("failed = :failed")
            params["failed"] = failed

        sql = text(
            f"""
            UPDATE notification_broadcasts
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, params)).mappings().first()
            if row is None:
                raise RuntimeError(f"Broadcast {broadcast_id} not found")
            return self._row_to_model(cast(Mapping[str, Any], row))

    async def get(self, broadcast_id: str) -> Broadcast | None:
        sql = text("SELECT * FROM notification_broadcasts WHERE id = :id")
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"id": broadcast_id})).mappings().first()
            return self._row_to_model(cast(Mapping[str, Any], row)) if row else None

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        statuses: Sequence[BroadcastStatus] | None = None,
        query: str | None = None,
    ) -> BroadcastCollection:
        filters: dict[str, Any] = {}
        conditions: list[str] = []

        if statuses:
            status_values = [status.value for status in statuses]
            if status_values:
                filters["status_values"] = status_values
                conditions.append("status = ANY(:status_values)")

        if query:
            filters["query"] = f"%{query}%"
            conditions.append(
                "(title ILIKE :query OR COALESCE(body, '') ILIKE :query OR CAST(template_id AS text) ILIKE :query OR created_by ILIKE :query)"
            )

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        list_params = {**filters, "limit": limit, "offset": offset}

        sql_list = text(
            f"""
            SELECT *
            FROM notification_broadcasts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        sql_count = text(
            f"""
            SELECT COUNT(*) AS total
            FROM notification_broadcasts
            {where_clause}
            """
        )
        sql_sum = text(
            f"""
            SELECT COALESCE(SUM(total), 0) AS total_recipients
            FROM notification_broadcasts
            {where_clause}
            """
        )
        sql_stats = text(
            f"""
            SELECT status, COUNT(*) AS count
            FROM notification_broadcasts
            {where_clause}
            GROUP BY status
            """
        )

        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql_list, list_params)).mappings().all()
            items = tuple(
                self._row_to_model(cast(Mapping[str, Any], row)) for row in rows
            )

            total_row = (await conn.execute(sql_count, filters)).first()
            total = int(total_row[0]) if total_row is not None else len(items)

            sum_row = (await conn.execute(sql_sum, filters)).first()
            recipient_total = int(sum_row[0]) if sum_row is not None else 0

            stats_rows = (await conn.execute(sql_stats, filters)).mappings().all()
            status_counts: dict[BroadcastStatus, int] = {
                status: 0 for status in BroadcastStatus
            }
            for row in stats_rows:
                try:
                    status = BroadcastStatus(str(row.get("status")))
                except ValueError:
                    continue
                status_counts[status] = int(row.get("count") or 0)

        return BroadcastCollection(
            items=items,
            total=total,
            status_counts=status_counts,
            recipient_total=recipient_total,
        )

    async def claim_due(
        self, now: datetime, limit: int = 10
    ) -> builtins.list[Broadcast]:
        if limit <= 0:
            return []
        scheduled = BroadcastStatus.SCHEDULED.value
        sending = BroadcastStatus.SENDING.value
        select_sql = text(
            """
            SELECT id
            FROM notification_broadcasts
            WHERE status = :scheduled
              AND scheduled_at IS NOT NULL
              AND scheduled_at <= :now
            ORDER BY scheduled_at ASC, created_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT :limit
            """
        )
        update_sql = text(
            """
            UPDATE notification_broadcasts
            SET status = :sending,
                started_at = COALESCE(started_at, :now),
                updated_at = now()
            WHERE id = :id
              AND status = :scheduled
              AND (scheduled_at IS NULL OR scheduled_at <= :now)
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            ids = (
                (
                    await conn.execute(
                        select_sql,
                        {"scheduled": scheduled, "now": now, "limit": limit},
                    )
                )
                .scalars()
                .all()
            )
            claimed: list[Broadcast] = []
            for identifier in ids:
                row = (
                    (
                        await conn.execute(
                            update_sql,
                            {
                                "id": identifier,
                                "now": now,
                                "scheduled": scheduled,
                                "sending": sending,
                            },
                        )
                    )
                    .mappings()
                    .first()
                )
                if row:
                    claimed.append(self._row_to_model(row))
            return claimed

    async def claim(self, broadcast_id: str, *, now: datetime) -> Broadcast | None:
        scheduled = BroadcastStatus.SCHEDULED.value
        sending = BroadcastStatus.SENDING.value
        update_sql = text(
            """
            UPDATE notification_broadcasts
            SET status = :sending,
                started_at = COALESCE(started_at, :now),
                updated_at = now()
            WHERE id = :id
              AND status = :scheduled
              AND (scheduled_at IS NULL OR scheduled_at <= :now)
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        update_sql,
                        {
                            "id": broadcast_id,
                            "now": now,
                            "scheduled": scheduled,
                            "sending": sending,
                        },
                    )
                )
                .mappings()
                .first()
            )
        if row is not None:
            return self._row_to_model(cast(Mapping[str, Any], row))
        return await self.get(broadcast_id)

    @staticmethod
    def _prepare_write_params(
        payload: BroadcastCreateModel | BroadcastUpdateModel, *, created: bool
    ) -> dict[str, Any]:
        audience = payload.audience
        audience_filters = (
            json.dumps(audience.filters) if audience.filters is not None else None
        )
        audience_user_ids = (
            json.dumps(list(audience.user_ids))
            if audience.user_ids is not None
            else None
        )
        params: dict[str, Any] = {
            "title": payload.title,
            "body": payload.body,
            "template_id": payload.template_id,
            "audience_type": audience.type.value,
            "audience_filters": audience_filters,
            "audience_user_ids": audience_user_ids,
            "status": payload.status.value,
            "scheduled_at": payload.scheduled_at,
        }
        if created and isinstance(payload, BroadcastCreateModel):
            params["created_by"] = payload.created_by
        return params

    @staticmethod
    def _row_to_model(row: Mapping[str, Any]) -> Broadcast:
        audience = BroadcastAudience(
            type=BroadcastAudienceType(row["audience_type"]),
            filters=row["audience_filters"],
            user_ids=row["audience_user_ids"],
        )
        return Broadcast(
            id=str(row["id"]),
            title=row["title"],
            body=row["body"],
            template_id=(
                str(row["template_id"]) if row["template_id"] is not None else None
            ),
            audience=audience,
            status=BroadcastStatus(row["status"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            scheduled_at=row["scheduled_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            total=row["total"],
            sent=row["sent"],
            failed=row["failed"],
        )


__all__ = ["SQLBroadcastRepo"]
