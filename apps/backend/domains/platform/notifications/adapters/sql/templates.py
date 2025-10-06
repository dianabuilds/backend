from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.domain.template import Template
from domains.platform.notifications.ports import TemplateRepo

from .._engine import ensure_async_engine


class SQLTemplateRepo(TemplateRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine = ensure_async_engine(engine)

    @staticmethod
    def _row_to_model(row: Any) -> Template:
        return Template(
            id=str(row["id"]),
            slug=str(row["slug"]),
            name=str(row["name"]),
            description=row["description"],
            subject=row["subject"],
            body=str(row["body"]),
            locale=row["locale"],
            variables=dict(row["variables"]) if row["variables"] is not None else None,
            meta=dict(row["meta"]) if row["meta"] is not None else None,
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def upsert(self, payload: dict[str, Any]) -> Template:
        sql = text(
            """
            INSERT INTO notification_templates (
              id,
              slug,
              name,
              description,
              subject,
              body,
              locale,
              variables,
              meta,
              created_by,
              created_at,
              updated_at
            ) VALUES (
              coalesce(:id, gen_random_uuid()),
              :slug,
              :name,
              :description,
              :subject,
              :body,
              :locale,
              :variables,
              :meta,
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
        ).bindparams(
            sa.bindparam("variables", type_=JSONB),
            sa.bindparam("meta", type_=JSONB),
        )
        data = dict(payload)
        for key in ("variables", "meta"):
            value = data.get(key)
            if value is None:
                data[key] = None
                continue
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    data[key] = None
                    continue
                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{key}_invalid_json") from exc
            if isinstance(value, Mapping):
                data[key] = dict(value)
            else:
                data[key] = value
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, data)).mappings().first()
            assert row is not None
            return self._row_to_model(row)

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
            return [self._row_to_model(row) for row in rows]

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


__all__ = ["SQLTemplateRepo"]
