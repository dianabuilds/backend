from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from apps.backend import get_container

from ...application.appeals.exceptions import ModerationAppealError
from ...application.appeals.repository import AppealsRepository, create_repository
from ...application.appeals.use_cases import (
    UseCaseResult,
)
from ...application.appeals.use_cases import (
    decide_appeal as decide_appeal_use_case,
)
from ...application.appeals.use_cases import (
    get_appeal as get_appeal_use_case,
)
from ...application.appeals.use_cases import (
    list_appeals as list_appeals_use_case,
)
from ...dtos import AppealDTO
from ..rbac import require_scopes

router = APIRouter(prefix="/appeals", tags=["moderation-appeals"])


def _build_repository(container) -> AppealsRepository:
    return create_repository(container.settings)


def _apply(result: UseCaseResult) -> dict[str, Any]:
    return result.payload


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
    repository = _build_repository(container)
    try:
        result = await list_appeals_use_case(
            container.platform_moderation.service,
            repository,
            status=status,
            user_id=user_id,
            target_type=target_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            cursor=cursor,
        )
    except ModerationAppealError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return _apply(result)


@router.get(
    "/{appeal_id}",
    response_model=AppealDTO,
    dependencies=[Depends(require_scopes("moderation:appeals:read"))],
)
async def get_appeal(appeal_id: str, container=Depends(get_container)) -> AppealDTO:
    repository = _build_repository(container)
    try:
        result = await get_appeal_use_case(
            container.platform_moderation.service,
            repository,
            appeal_id,
        )
    except ModerationAppealError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return AppealDTO.model_validate(result.payload)


@router.post(
    "/{appeal_id}/decision",
    dependencies=[Depends(require_scopes("moderation:appeals:decide:write"))],
)
async def decide_appeal(
    appeal_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> dict[str, Any]:
    repository = _build_repository(container)
    try:
        result = await decide_appeal_use_case(
            container.platform_moderation.service,
            repository,
            appeal_id=appeal_id,
            payload=body,
            actor_id=body.get("actor_id"),
        )
    except ModerationAppealError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return _apply(result)


__all__ = ["router"]
