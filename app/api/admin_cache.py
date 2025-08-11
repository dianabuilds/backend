import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.services.navcache import navcache
from app.core.log_events import cache_counters, cache_key_hits

router = APIRouter(prefix="/admin/cache", tags=["admin"])
logger = logging.getLogger(__name__)


class InvalidatePatternRequest(BaseModel):
    pattern: str


@router.get("/stats", summary="Cache statistics")
async def cache_stats(
    current_user: User = Depends(require_role("moderator")),
):
    counters = {k: dict(v) for k, v in cache_counters.items()}
    hot_keys = []
    for key, count in cache_key_hits.most_common(10):
        ttl = await navcache._cache.ttl(key)
        hot_keys.append({"key": key, "count": count, "ttl": ttl})
    return {"counters": counters, "hot_keys": hot_keys}


@router.post("/invalidate_by_pattern", summary="Invalidate cache by pattern")
async def invalidate_by_pattern(
    payload: InvalidatePatternRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    keys = await navcache._cache.scan(payload.pattern)
    await navcache._cache.delete_many(keys)
    logger.info(
        "admin_action",
        extra={
            "action": "cache_invalidate_pattern",
            "actor_id": str(current_user.id),
            "pattern": payload.pattern,
            "deleted": len(keys),
        },
    )
    return {"deleted": len(keys)}
