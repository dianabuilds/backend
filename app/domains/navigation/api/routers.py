from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.api.transitions import router as transitions_router  # noqa: E402
from app.api.navigation import router as navigation_router  # noqa: E402
from app.api.admin_navigation import router as admin_navigation_router  # noqa: E402

router.include_router(transitions_router)
router.include_router(navigation_router)
router.include_router(admin_navigation_router)
