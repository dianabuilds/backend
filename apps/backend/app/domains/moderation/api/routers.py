from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.domains.moderation.api.cases_router import (  # noqa: E402
    router as admin_moderation_cases_router,
)
from app.domains.moderation.api.restrictions_router import (  # noqa: E402
    router as moderation_router,
)
from app.domains.moderation.api.queue_router import (  # noqa: E402
    router as moderation_queue_router,
)

router.include_router(moderation_router)
router.include_router(admin_moderation_cases_router)
router.include_router(moderation_queue_router)

__all__ = ["router"]
