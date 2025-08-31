from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.log_events import cache_counters, cache_key_hits
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()
admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/cache",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)
logger = logging.getLogger(__name__)

navcache = NavigationCacheService(CoreCacheAdapter())


class InvalidatePatternRequest(BaseModel):
    pattern: str


@router.get("/stats", summary="Cache statistics")
async def cache_stats(
    current_user: User = Depends(admin_required),
):
    counters = {k: dict(v) for k, v in cache_counters.items()}
    hot_keys = []
    for key, count in cache_key_hits.most_common(10):
        ttl = None
        hot_keys.append({"key": key, "count": count, "ttl": ttl})
    return {"counters": counters, "hot_keys": hot_keys}


@router.post("/invalidate_by_pattern", summary="Invalidate cache by pattern")
async def invalidate_by_pattern(
    payload: InvalidatePatternRequest,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    keys = await navcache._cache.scan(payload.pattern)
    if keys:
        await navcache._cache.delete(*keys)
    logger.info(
        "admin_action",
        extra={
            "action": "cache_invalidate_pattern",
            "actor_id": str(current_user.id),
            "pattern": payload.pattern,
            "deleted": len(keys or []),
        },
    )
    return {"deleted": len(keys or [])}
