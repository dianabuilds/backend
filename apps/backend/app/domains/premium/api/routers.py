from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.domains.premium.api.public_router import (  # noqa: E402
    router as premium_limits_router,
)

router.include_router(premium_limits_router)

__all__ = ["router"]
