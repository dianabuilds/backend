from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(
    prefix="/admin/moderation/cases",
    tags=["admin-moderation"],
)

# TODO: implement endpoints for moderation cases

__all__ = ["router"]
