"""Simple helper for inserting events into the outbox table."""

from datetime import datetime
from uuid import uuid4
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.outbox_models import OutboxEvent, OutboxStatus


async def emit(
    db: AsyncSession,
    topic: str,
    payload: Dict[str, Any],
    dedup_key: Optional[str] = None,
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
    )
    db.add(event)
    await db.flush()
    return event
