from __future__ import annotations

import builtins
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backendDDD.domains.platform.notifications.domain.campaign import Campaign
from apps.backendDDD.domains.platform.notifications.ports import CampaignRepo


class SQLCampaignRepo(CampaignRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    def _row_to_model(self, r: Any) -> Campaign:
        return Campaign(
            id=str(r["id"]),
            title=str(r["title"]),
            message=str(r["message"]),
            type=str(r["type"]),
            filters=(dict(r["filters"]) if r["filters"] is not None else None),
            status=str(r["status"]),
            total=int(r["total"]),
            sent=int(r["sent"]),
            failed=int(r["failed"]),
            created_by=str(r["created_by"]),
            created_at=r["created_at"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
        )

    async def upsert(self, payload: dict[str, Any]) -> Campaign:
        sql = text(
            """
            INSERT INTO notification_campaigns(id, title, message, type, filters, status, total, sent, failed, created_by, created_at, started_at, finished_at)
            VALUES (coalesce(:id, gen_random_uuid()), :title, :message, coalesce(:type,'platform'), cast(:filters as jsonb), coalesce(:status,'draft'), coalesce(:total,0), coalesce(:sent,0), coalesce(:failed,0), :created_by, now(), :started_at, :finished_at)
            ON CONFLICT (id) DO UPDATE SET
                title = excluded.title,
                message = excluded.message,
                type = excluded.type,
                filters = excluded.filters,
                status = excluded.status,
                total = excluded.total,
                sent = excluded.sent,
                failed = excluded.failed,
                started_at = excluded.started_at,
                finished_at = excluded.finished_at
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, payload)).mappings().first()
            assert r is not None
            return self._row_to_model(r)

    async def list(self, limit: int = 50, offset: int = 0) -> builtins.list[Campaign]:
        sql = text(
            "SELECT * FROM notification_campaigns ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )
        async with self._engine.begin() as conn:
            rows = (
                (await conn.execute(sql, {"limit": int(limit), "offset": int(offset)}))
                .mappings()
                .all()
            )
            return [self._row_to_model(r) for r in rows]

    async def get(self, campaign_id: str) -> Campaign | None:
        sql = text("SELECT * FROM notification_campaigns WHERE id = :id")
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": campaign_id})).mappings().first()
            if not r:
                return None
            return self._row_to_model(r)

    async def delete(self, campaign_id: str) -> None:
        sql = text("DELETE FROM notification_campaigns WHERE id = :id")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": campaign_id})


__all__ = ["SQLCampaignRepo"]
