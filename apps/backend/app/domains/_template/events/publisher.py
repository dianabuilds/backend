from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel.outbox import emit as outbox_emit


async def publish_created(
    db: AsyncSession,
    *,
    payload: dict[str, Any],
    tenant_id: UUID | None = None,
) -> None:
    await outbox_emit(db, topic="event.{{domain}}.created.v1", payload=payload, tenant_id=tenant_id)

__all__ = ["publish_created"]
