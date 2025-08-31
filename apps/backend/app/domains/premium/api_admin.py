from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/premium", tags=["admin-premium"])

# TODO: implement premium admin endpoints

__all__ = ["router"]
