from __future__ import annotations

from fastapi import APIRouter

from app.domains.premium.api.public_router import router as premium_limits_router

router = APIRouter()

router.include_router(premium_limits_router)

__all__ = ["router"]
