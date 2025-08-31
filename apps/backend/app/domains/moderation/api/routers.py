from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.api.admin_moderation_cases import (  # noqa: E402
    router as admin_moderation_cases_router,
)
from app.api.moderation import router as moderation_router  # noqa: E402
from app.domains.moderation.api.queue_router import (  # noqa: E402
    router as moderation_queue_router,
)

router.include_router(moderation_router)
router.include_router(admin_moderation_cases_router)
router.include_router(moderation_queue_router)
