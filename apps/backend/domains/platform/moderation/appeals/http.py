from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException

from ..dtos import AppealDTO
from ..rbac import require_scopes

router = APIRouter(prefix="/appeals", tags=["moderation-appeals"])


@router.get("", dependencies=[Depends(require_scopes("moderation:appeals:read"))])
async def list_appeals(
    status: str | None = None,
    user_id: str | None = None,
    target_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    # No SQL storage for appeals; return empty list for real-data mode
    return {"items": [], "next_cursor": None}


@router.get(
    "/{appeal_id}",
    response_model=AppealDTO,
    dependencies=[Depends(require_scopes("moderation:appeals:read"))],
)
async def get_appeal(appeal_id: str, container=Depends(get_container)) -> AppealDTO:
    svc = container.platform_moderation.service
    try:
        return await svc.get_appeal(appeal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="appeal_not_found") from exc


@router.post(
    "/{appeal_id}/decision",
    dependencies=[Depends(require_scopes("moderation:appeals:decide:write"))],
)
async def decide_appeal(
    appeal_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        return await svc.decide_appeal(appeal_id, body, actor_id=body.get("actor_id"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="appeal_not_found") from exc


__all__ = ["router"]
