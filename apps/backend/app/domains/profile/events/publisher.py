from __future__ import annotations

import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession


async def publish_profile_updated(
    db: AsyncSession, *, profile: dict, tenant_id: UUID | None = None
) -> None:
    # Compute a stable hash for deduplication (avoid duplicates on retries)
    try:
        normalized = json.dumps(profile, sort_keys=True, default=str)
        etag = hashlib.md5(normalized.encode()).hexdigest()
    except Exception:
        etag = ""
    user_or_profile_id = str(profile.get("id") or profile.get("user_id") or "")
    dedup = f"profile:{user_or_profile_id}:{etag}"

    payload = {
        "eventId": str(uuid4()),
        "occurredAt": datetime.utcnow().isoformat(),
        "profile": profile,
    }

    # Lazy import to avoid heavy imports at module import time
    from app.domains.system.platform.outbox import emit as outbox_emit

    await outbox_emit(
        db,
        topic="event.profile.updated.v1",
        payload=payload,
        tenant_id=tenant_id,
        dedup_key=dedup,
    )

__all__ = ["publish_profile_updated"]
