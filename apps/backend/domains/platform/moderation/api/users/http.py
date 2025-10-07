from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.users import commands as user_commands
from ...application.users import queries as user_queries
from ...application.users.exceptions import ModerationUserError, UserNotFoundError
from ...application.users.presenter import (
    ModeratorNotePayload,
    RolesUpdateResponse,
    SanctionResponse,
    UserDetailPayload,
    UsersListResponse,
)
from ...application.users.repository import ModerationUsersRepository, create_repository
from ..rbac import require_scopes

router = APIRouter(prefix="/users", tags=["moderation-users"])


def _build_repository(container) -> ModerationUsersRepository:
    return create_repository(getattr(container, "settings", None))


def _extract_notifications(container: Any) -> Any | None:
    notifications = getattr(container, "notifications", None)
    if notifications is None:
        return None
    return getattr(notifications, "notify", notifications)


@router.get(
    "",
    dependencies=[Depends(require_scopes("moderation:users:read"))],
)
async def list_users(
    status: str | None = None,
    role: str | None = None,
    registered_from: str | None = None,
    registered_to: str | None = None,
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
    container=Depends(get_container),
) -> UsersListResponse:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    return await user_queries.list_users_view(
        svc,
        settings=container.settings,
        repository=repository,
        status=status,
        role=role,
        registered_from=registered_from,
        registered_to=registered_to,
        q=q,
        limit=limit,
        cursor=cursor,
    )


@router.get(
    "/{user_id}",
    dependencies=[Depends(require_scopes("moderation:users:read"))],
)
async def get_user(
    user_id: str,
    container=Depends(get_container),
) -> UserDetailPayload:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        return await user_queries.get_user_view(
            svc,
            user_id,
            settings=container.settings,
            repository=repository,
        )
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="user_not_found") from error


@router.post(
    "/{user_id}/roles",
    dependencies=[Depends(require_scopes("moderation:users:roles:write"))],
)
async def update_roles(
    user_id: str,
    body: Mapping[str, Any],
    container=Depends(get_container),
) -> RolesUpdateResponse:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        return await user_commands.update_roles_command(
            svc,
            user_id,
            body,
            settings=container.settings,
            repository=repository,
        )
    except ModerationUserError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="user_not_found") from error


@router.post(
    "/{user_id}/sanctions",
    dependencies=[Depends(require_scopes("moderation:users:sanctions:write"))],
)
async def issue_sanction(
    user_id: str,
    body: Mapping[str, Any],
    container=Depends(get_container),
) -> SanctionResponse:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    notifications = _extract_notifications(container)
    try:
        return await user_commands.issue_sanction(
            svc,
            user_id,
            body,
            settings=container.settings,
            notifications=notifications,
            repository=repository,
            idempotency_key=body.get("idempotency_key"),
        )
    except ModerationUserError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="user_not_found") from error


@router.patch(
    "/{user_id}/sanctions/{sanction_id}",
    dependencies=[Depends(require_scopes("moderation:users:sanctions:write"))],
)
async def update_sanction(
    user_id: str,
    sanction_id: str,
    body: Mapping[str, Any],
    container=Depends(get_container),
) -> SanctionResponse:
    svc = container.platform_moderation.service
    try:
        return await user_commands.update_sanction(
            svc,
            user_id,
            sanction_id,
            body,
        )
    except ModerationUserError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error


@router.post(
    "/{user_id}/notes",
    dependencies=[Depends(require_scopes("moderation:users:notes:write"))],
)
async def add_note(
    user_id: str,
    body: Mapping[str, Any],
    container=Depends(get_container),
) -> ModeratorNotePayload:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        return await user_commands.add_note(
            svc,
            user_id,
            body,
            settings=container.settings,
            repository=repository,
        )
    except ModerationUserError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="user_not_found") from error


__all__ = ["router"]
