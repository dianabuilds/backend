from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.api.moderation import router as moderation_router  # noqa: E402
from app.api.admin_moderation_cases import router as admin_moderation_cases_router  # noqa: E402

router.include_router(moderation_router)
router.include_router(admin_moderation_cases_router)
