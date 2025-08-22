from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.api.premium_limits import router as premium_limits_router  # noqa: E402
from app.api.admin_premium import router as admin_premium_router  # noqa: E402

router.include_router(premium_limits_router)
router.include_router(admin_premium_router)
