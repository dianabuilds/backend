from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/tags", tags=["tags"])

# Include public endpoints for tags
from app.domains.tags.api.public_router import (
    router as public_tags_router,  # noqa: E402
)

router.include_router(public_tags_router)


@router.get("/_health")
async def tags_health() -> dict[str, str]:
    return {"status": "ok"}
