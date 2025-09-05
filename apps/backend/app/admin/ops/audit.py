from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin/audit", tags=["admin"])


@router.get("/")
async def get_audit(actor: str | None = None, action: str | None = None) -> dict[str, object]:
    """Return audit log entries with optional filters."""
    filters = {"actor": actor, "action": action}
    return {"items": [], "filters": filters}
