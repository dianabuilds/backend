from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from app.domains.media.api.media_router import router as media_router  # noqa: E402

router.include_router(media_router)
