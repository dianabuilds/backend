from __future__ import annotations

from fastapi import APIRouter

try:
    from ...overview.http import router as _router
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    router = APIRouter(prefix="/overview", tags=["moderation-overview"])
else:  # pragma: no cover - thin re-export
    router = _router

__all__ = ["router"]
