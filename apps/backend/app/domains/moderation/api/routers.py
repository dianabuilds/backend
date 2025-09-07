from __future__ import annotations

from fastapi import APIRouter

from app.domains.moderation.api.cases_router import router as moderation_cases_router
from app.domains.moderation.api.public_router import router as moderation_public_router
from app.domains.moderation.api.queue_router import router as moderation_queue_router
from app.domains.moderation.api.restrictions_router import (
    router as moderation_router,
)

router = APIRouter()

router.include_router(moderation_router)
router.include_router(moderation_queue_router)
router.include_router(moderation_cases_router)
router.include_router(moderation_public_router)

__all__ = ["router"]
