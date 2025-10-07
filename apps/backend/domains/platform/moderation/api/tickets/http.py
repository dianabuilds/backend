from __future__ import annotations

from fastapi import APIRouter

try:
    from ...tickets.http import router as _router
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    router = APIRouter(prefix="/tickets", tags=["moderation-tickets"])
else:  # pragma: no cover - thin re-export
    router = _router

__all__ = ["router"]
