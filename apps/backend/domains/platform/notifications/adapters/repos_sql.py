from __future__ import annotations

import builtins
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.notifications.domain.campaign import Campaign
from domains.platform.notifications.domain.template import Template
from domains.platform.notifications.ports import CampaignRepo, TemplateRepo


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
            template_id=(str(r["template_id"]) if r["template_id"] is not None else None),
            created_by=str(r["created_by"]),
            created_at=r["created_at"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
        )

    async def upsert(self, payload: dict[str, Any]) -> Campaign:
        sql = text(
            """
            INSERT INTO notification_campaigns(
              id, title, message, type, filters, status, total, sent, failed, template_id, created_by, created_at, started_at, finished_at
            ) VALUES (
              coalesce(:id, gen_random_uuid()),
              :title,
              :message,
              coalesce(:type,'platform'),
              cast(:filters as jsonb),
              coalesce(:status,'draft'),
              coalesce(:total,0),
              coalesce(:sent,0),
              coalesce(:failed,0),
              :template_id,
              :created_by,
              now(),
              :started_at,
              :finished_at
            )
            ON CONFLICT (id) DO UPDATE SET
                title = excluded.title,
                message = excluded.message,
                type = excluded.type,
                filters = excluded.filters,
                status = excluded.status,
                total = excluded.total,
                sent = excluded.sent,
                failed = excluded.failed,
                template_id = excluded.template_id,
                started_at = excluded.started_at,
                finished_at = excluded.finished_at
            RETURNING *
            """
        )
        data = dict(payload)
        if "template_id" not in data:
            data["template_id"] = None
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, data)).mappings().first()
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


class SQLTemplateRepo(TemplateRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    def _row_to_model(self, r: Any) -> Template:
        return Template(
            id=str(r["id"]),
            slug=str(r["slug"]),
            name=str(r["name"]),
            description=r["description"],
            subject=r["subject"],
            body=str(r["body"]),
            locale=r["locale"],
            variables=dict(r["variables"]) if r["variables"] is not None else None,
            meta=dict(r["meta"]) if r["meta"] is not None else None,
            created_by=r["created_by"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )

    async def upsert(self, payload: dict[str, Any]) -> Template:
        sql = text(
            """
            INSERT INTO notification_templates(
              id, slug, name, description, subject, body, locale, variables, meta, created_by, created_at, updated_at
            ) VALUES (
              coalesce(:id, gen_random_uuid()),
              :slug,
              :name,
              :description,
              :subject,
              :body,
              :locale,
              CASE WHEN :variables IS NULL THEN NULL ELSE cast(:variables AS jsonb) END,
              CASE WHEN :meta IS NULL THEN NULL ELSE cast(:meta AS jsonb) END,
              :created_by,
              coalesce(:created_at, now()),
              now()
            )
            ON CONFLICT (id) DO UPDATE SET
              slug = excluded.slug,
              name = excluded.name,
              description = excluded.description,
              subject = excluded.subject,
              body = excluded.body,
              locale = excluded.locale,
              variables = excluded.variables,
              meta = excluded.meta,
              created_by = excluded.created_by,
              updated_at = now()
            RETURNING *
            """
        )
        data = dict(payload)
        for key in ("variables", "meta"):
            value = data.get(key)
            if value is None:
                data[key] = None
            elif isinstance(value, str):
                data[key] = value
            else:
                data[key] = json.dumps(value)
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, data)).mappings().first()
            assert r is not None
            return self._row_to_model(r)

    async def list(self, limit: int = 50, offset: int = 0) -> list[Template]:
        sql = text(
            "SELECT * FROM notification_templates ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"
        )
        async with self._engine.begin() as conn:
            rows = (
                (await conn.execute(sql, {"limit": int(limit), "offset": int(offset)}))
                .mappings()
                .all()
            )
            return [self._row_to_model(r) for r in rows]

    async def get(self, template_id: str) -> Template | None:
        sql = text("SELECT * FROM notification_templates WHERE id = :id")
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"id": template_id})).mappings().first()
            return self._row_to_model(row) if row else None

    async def get_by_slug(self, slug: str) -> Template | None:
        sql = text("SELECT * FROM notification_templates WHERE slug = :slug")
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"slug": slug})).mappings().first()
            return self._row_to_model(row) if row else None

    async def delete(self, template_id: str) -> None:
        sql = text("DELETE FROM notification_templates WHERE id = :id")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": template_id})


__all__ = ["SQLCampaignRepo", "SQLTemplateRepo"]
