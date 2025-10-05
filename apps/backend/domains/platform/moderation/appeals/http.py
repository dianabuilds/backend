from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException

from ..api.rbac import require_scopes
from ..application.appeals import commands as appeal_commands
from ..application.appeals import queries as appeal_queries
from ..application.appeals.repository import AppealsRepository, create_repository
from ..dtos import AppealDTO

router = APIRouter(prefix="/appeals", tags=["moderation-appeals"])


def _build_repository(container) -> AppealsRepository:
    return create_repository(container.settings)


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
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    return await appeal_queries.list_appeals(
        svc,
        status=status,
        user_id=user_id,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        repository=repository,
    )


@router.get(
    "/{appeal_id}",
    response_model=AppealDTO,
    dependencies=[Depends(require_scopes("moderation:appeals:read"))],
)
async def get_appeal(appeal_id: str, container=Depends(get_container)) -> AppealDTO:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        result = await appeal_queries.get_appeal(svc, appeal_id, repository=repository)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="appeal_not_found") from exc
    if isinstance(result, AppealDTO):
        return result
    return AppealDTO.model_validate(result)


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
    repository = _build_repository(container)
    try:
        return await appeal_commands.decide_appeal(
            svc,
            appeal_id,
            body,
            actor_id=body.get("actor_id"),
            repository=repository,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="appeal_not_found") from exc


__all__ = ["router"]
