from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, Header, HTTPException

from ..api.rbac import require_scopes
from ..application.users.exceptions import ModerationUserError, UserNotFoundError
from ..application.users.use_cases import (
    UseCaseResult,
    update_roles_use_case,
)
from ..application.users.use_cases import (
    add_note as add_note_use_case,
)
from ..application.users.use_cases import (
    get_user as get_user_use_case,
)
from ..application.users.use_cases import (
    issue_sanction as issue_sanction_use_case,
)
from ..application.users.use_cases import (
    list_users as list_users_use_case,
)
from ..application.users.use_cases import (
    update_sanction as update_sanction_use_case,
)
from ..domain.dtos import SanctionDTO, UserDetail

router = APIRouter(prefix="/users", tags=["moderation-users"])


def _apply(result: UseCaseResult, *, model=None) -> Any:
    payload = result.payload
    if model is not None and hasattr(model, "model_validate"):
        return model.model_validate(payload)
    return payload


def _handle_errors(error: Exception) -> None:
    if isinstance(error, UserNotFoundError):
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    if isinstance(error, ModerationUserError):
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    raise error


@router.get("", dependencies=[Depends(require_scopes("moderation:users:read"))])
async def list_users(
    status: str | None = None,
    role: str | None = None,
    registered_from: str | None = None,
    registered_to: str | None = None,
    q: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        result = await list_users_use_case(
            svc,
            container.settings,
            status=status,
            role=role,
            registered_from=registered_from,
            registered_to=registered_to,
            q=q,
            limit=limit,
            cursor=cursor,
        )
    except Exception as exc:  # pragma: no cover - thin wrapper
        _handle_errors(exc)
    return _apply(result)


@router.get(
    "/{user_id}",
    response_model=UserDetail,
    dependencies=[Depends(require_scopes("moderation:users:read"))],
)
async def get_user(user_id: str, container=Depends(get_container)) -> UserDetail:
    svc = container.platform_moderation.service
    try:
        result = await get_user_use_case(svc, container.settings, user_id)
    except Exception as exc:
        _handle_errors(exc)
    return _apply(result, model=UserDetail)


@router.post(
    "/{user_id}/roles",
    dependencies=[Depends(require_scopes("moderation:users:roles:write"))],
)
async def update_roles(
    user_id: str, body: Mapping[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        result = await update_roles_use_case(svc, container.settings, user_id, body)
    except Exception as exc:
        _handle_errors(exc)
    return _apply(result)


@router.post(
    "/{user_id}/sanctions",
    response_model=SanctionDTO,
    dependencies=[Depends(require_scopes("moderation:users:sanctions:write"))],
)
async def issue_sanction(
    user_id: str,
    body: Mapping[str, Any],
    container=Depends(get_container),
    idempotency_key: str | None = Header(
        default=None, convert_underscores=False, alias="Idempotency-Key"
    ),
) -> SanctionDTO:
    svc = container.platform_moderation.service
    notifications = getattr(getattr(container, "notifications", None), "notify", None)
    try:
        result = await issue_sanction_use_case(
            svc,
            container.settings,
            notifications,
            user_id,
            body,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        _handle_errors(exc)
    return _apply(result, model=SanctionDTO)


@router.patch(
    "/{user_id}/sanctions/{sanction_id}",
    response_model=SanctionDTO,
    dependencies=[Depends(require_scopes("moderation:users:sanctions:write"))],
)
async def update_sanction(
    user_id: str,
    sanction_id: str,
    body: Mapping[str, Any],
    container=Depends(get_container),
) -> SanctionDTO:
    svc = container.platform_moderation.service
    try:
        result = await update_sanction_use_case(svc, user_id, sanction_id, body)
    except Exception as exc:
        _handle_errors(exc)
    return _apply(result, model=SanctionDTO)


@router.post(
    "/{user_id}/notes",
    dependencies=[Depends(require_scopes("moderation:users:notes:write"))],
)
async def add_note(
    user_id: str, body: Mapping[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        result = await add_note_use_case(svc, container.settings, user_id, body)
    except Exception as exc:
        _handle_errors(exc)
    return _apply(result)


__all__ = ["router"]
