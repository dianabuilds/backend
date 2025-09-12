from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import NavCacheInvalidated, Scope


TopicNavInvalidated = Literal["event.navigation.cache.invalidated.v1"]


def _dedup_for(payload: NavCacheInvalidated) -> str:
    user = str(payload.user_id) if payload.user_id is not None else "all"
    node = str(payload.node_id) if payload.node_id is not None else ""
    slug = payload.slug or ""
    return f"navinvalidate:{payload.scope}:{user}:{node}:{slug}:{payload.reason}"


async def publish_nav_cache_invalidated(
    db: AsyncSession,
    *,
    scope: Scope,
    reason: str,
    user_id: UUID | None = None,
    node_id: int | None = None,
    slug: str | None = None,
) -> None:
    payload = NavCacheInvalidated(
        scope=scope,
        reason=reason,
        user_id=user_id,
        node_id=node_id,
        slug=slug,
    )
    # Lazy import to avoid heavy imports at module import time
    from app.domains.system.platform.outbox import emit as outbox_emit

    await outbox_emit(
        db,
        topic="event.navigation.cache.invalidated.v1",
        payload={
            "scope": payload.scope,
            "reason": payload.reason,
            "user_id": str(payload.user_id) if payload.user_id is not None else None,
            "node_id": payload.node_id,
            "slug": payload.slug,
        },
        tenant_id=None,
        dedup_key=_dedup_for(payload),
    )


__all__ = ["publish_nav_cache_invalidated"]
