from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from uuid import UUID

import sqlalchemy as sa

from ..tables import SITE_AUDIT_LOG_TABLE

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class AuditRepositoryMixin:
    if TYPE_CHECKING:

        async def _require_engine(self) -> AsyncEngine: ...

    async def list_audit(
        self,
        *,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        actor: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Mapping[str, Any]], int]:
        engine = await self._require_engine()
        stmt = sa.select(SITE_AUDIT_LOG_TABLE).order_by(SITE_AUDIT_LOG_TABLE.c.created_at.desc())
        filters: list[Any] = []
        if entity_type:
            filters.append(SITE_AUDIT_LOG_TABLE.c.entity_type == entity_type)
        if entity_id:
            filters.append(SITE_AUDIT_LOG_TABLE.c.entity_id == entity_id)
        if actor:
            filters.append(SITE_AUDIT_LOG_TABLE.c.actor == actor)
        if filters:
            stmt = stmt.where(sa.and_(*filters))
        stmt = stmt.limit(limit).offset(offset)
        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.mappings().all()
            total_result = await conn.execute(
                sa.select(sa.func.count())
                .select_from(SITE_AUDIT_LOG_TABLE)
                .where(sa.and_(*filters) if filters else sa.true())
            )
            total = int(total_result.scalar_one())
        return rows, total


__all__ = ["AuditRepositoryMixin"]
