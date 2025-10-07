from __future__ import annotations

from fastapi import APIRouter

try:
    from ...ai_rules.http import router as _router
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    router = APIRouter(prefix="/ai-rules", tags=["moderation-ai-rules"])
else:  # pragma: no cover - thin re-export
    router = _router

__all__ = ["router"]
