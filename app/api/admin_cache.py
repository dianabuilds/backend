from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_role
from app.core.config import settings
from app.core.log_events import cache_invalidate
from app.models.user import User
from app.services.navcache import navcache


router = APIRouter(prefix="/admin/cache", tags=["admin"])


class InvalidatePatternRequest(BaseModel):
    pattern: str


@router.get("/stats", summary="Cache statistics")
async def cache_stats(
    current_user: User = Depends(require_role("moderator")),
):
    nav_keys = await navcache._cache.scan(f"{settings.cache.key_version}:nav*")
    comp_keys = await navcache._cache.scan(f"{settings.cache.key_version}:comp*")
    return {
        "nav_keys": len(nav_keys),
        "compass_keys": len(comp_keys),
        "nav_ttl": settings.cache.nav_cache_ttl,
        "compass_ttl": settings.cache.compass_cache_ttl,
        "hot_keys": [],
    }


@router.post(
    "/invalidate_by_pattern",
    summary="Invalidate cache keys by pattern",
)
async def invalidate_by_pattern(
    payload: InvalidatePatternRequest,
    current_user: User = Depends(require_role("admin")),
):
    keys = await navcache._cache.scan(payload.pattern)
    await navcache._cache.delete_many(keys)
    for key in keys:
        cache_invalidate("generic", reason="pattern", key=key)
    return {"deleted": len(keys)}
