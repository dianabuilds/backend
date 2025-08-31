"""Simple helper for inserting events into the outbox table."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox_models import OutboxEvent, OutboxStatus
from app.core.preview import PreviewContext


async def emit(
    db: AsyncSession,
    topic: str,
    payload: dict[str, Any],
    workspace_id: UUID,
    dedup_key: str | None = None,
    preview: PreviewContext | None = None,
) -> OutboxEvent:
    """Insert an event into the transactional outbox.

    The event is inserted in the provided database session. Caller is
    responsible for committing the transaction.
    """
    event = OutboxEvent(
        id=uuid4(),
        topic=topic,
        payload_json=payload,
        dedup_key=dedup_key,
        status=OutboxStatus.NEW,
        attempts=0,
        next_retry_at=datetime.utcnow(),
        workspace_id=workspace_id,
        is_preview=bool(preview and preview.mode == "shadow"),
    )
    db.add(event)
    await db.flush()
    return event
