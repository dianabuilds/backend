from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jsonschema import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

# NOTE: Profiles API reuses the existing accounts service and schemas.
# This provides a clean /profiles surface while backend internals are
# still transitioning away from the legacy "accounts" naming.
from app.domains.accounts.application.service import AccountService
from app.domains.accounts.infrastructure.dao import AccountDAO
from app.domains.accounts.infrastructure.models import AccountMember
from app.providers.db.pagination import parse_page_query
from app.providers.db.session import get_db
from app.schemas.accounts import (
    AccountCursorPage,
    AccountIn,
    AccountMemberIn,
    AccountMemberOut,
    AccountOut,
    AccountSettings,
    AccountUpdate,
    AccountWithRoleOut,
)
from app.schemas.notification import NotificationType
from app.schemas.notification_rules import NotificationRules
from app.domains.users.infrastructure.models.user import User
from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.notifications.validation import validate_notification_rules
from app.security import ADMIN_AUTH_RESPONSES, auth_user


# User-facing Profiles routes (equivalent of /accounts for now)
user_router = APIRouter(prefix="/profiles", tags=["profiles"])


@user_router.get("/", response_model=list[AccountWithRoleOut], summary="List user profiles")
async def list_user_profiles(
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[AccountWithRoleOut]:
    return await AccountService.list_for_user(db, user)


# Admin Profiles routes (equivalent of /admin/accounts for now)
router = APIRouter(
    prefix="/admin/profiles",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


# Dependency wrappers to bridge profile_id -> account_id
async def require_profile_editor(
    profile_id: int,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from app.domains.accounts.application.service import require_account_editor

    return await require_account_editor(profile_id, user, db)


async def require_profile_owner(
    profile_id: int,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from app.domains.accounts.application.service import require_account_owner

    return await require_account_owner(profile_id, user, db)


async def require_profile_viewer(
    profile_id: int,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from app.domains.accounts.application.service import require_account_viewer

    return await require_account_viewer(profile_id, user, db)


@router.post("", response_model=AccountOut, status_code=201, summary="Create profile")
async def create_profile(
    data: AccountIn,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountOut:
    account = await AccountService.create(db, data=data, owner=user)
    return account


@router.get("", response_model=AccountCursorPage, summary="List profiles")
async def list_profiles(
    request: Request,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountCursorPage:
    params: Mapping[str, str] = dict(request.query_params)
    pq = parse_page_query(
        params,
        allowed_sort=["created_at"],
        default_sort="created_at",
    )
    return await AccountService.list_paginated(db, user=user, pq=pq)


@router.get("/{profile_id}", response_model=AccountOut, summary="Get profile")
async def get_profile(
    profile_id: int,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountOut:
    return await AccountService.get_for_user(db, profile_id, user)


@router.patch("/{profile_id}", response_model=AccountOut, summary="Update profile")
async def update_profile(
    profile_id: int,
    data: AccountUpdate,
    _: Annotated[AccountMember | None, Depends(require_profile_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountOut:
    return await AccountService.update(db, profile_id, data)


@router.delete("/{profile_id}", status_code=204, summary="Delete profile")
async def delete_profile(
    profile_id: int,
    _: Annotated[AccountMember | None, Depends(require_profile_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await AccountService.delete(db, profile_id)
    return Response(status_code=204)


@router.post(
    "/{profile_id}/members",
    response_model=AccountMemberOut,
    status_code=201,
    summary="Add profile member",
)
async def add_member(
    profile_id: int,
    data: AccountMemberIn,
    _: Annotated[AccountMember | None, Depends(require_profile_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMemberOut:
    return await AccountService.add_member(db, profile_id, data)


@router.patch(
    "/{profile_id}/members/{user_id}",
    response_model=AccountMemberOut,
    summary="Update profile member",
)
async def update_member(
    profile_id: int,
    user_id: UUID,
    data: AccountMemberIn,
    _: Annotated[AccountMember | None, Depends(require_profile_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMemberOut:
    if data.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    return await AccountService.update_member(db, profile_id, user_id, data.role)


@router.delete(
    "/{profile_id}/members/{user_id}",
    status_code=204,
    summary="Remove profile member",
)
async def remove_member(
    profile_id: int,
    user_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_profile_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await AccountService.remove_member(db, profile_id, user_id)
    return Response(status_code=204)


@router.get(
    "/{profile_id}/members",
    response_model=list[AccountMemberOut],
    summary="List profile members",
)
async def list_members(
    profile_id: int,
    _: Annotated[AccountMember | None, Depends(require_profile_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[AccountMemberOut]:
    return await AccountService.list_members(db, profile_id)


@router.get(
    "/{profile_id}/settings/ai-presets",
    response_model=dict[str, Any],
    summary="Get profile AI presets",
)
async def get_ai_presets(
    profile_id: int,
    _: Annotated[AccountMember | None, Depends(require_profile_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    return await AccountService.get_ai_presets(db, profile_id)


@router.put(
    "/{profile_id}/settings/ai-presets",
    response_model=dict[str, Any],
    summary="Update profile AI presets",
)
async def put_ai_presets(
    profile_id: int,
    presets: dict[str, Any],
    _: Annotated[AccountMember | None, Depends(require_profile_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    account = await AccountDAO.get(db, profile_id)
    if not account:
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        from app.domains.ai.validation import validate_ai_presets

        validate_ai_presets(presets)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    settings = AccountSettings.model_validate(account.settings_json)
    settings.ai_presets = presets
    account.settings_json = settings.model_dump()
    await db.commit()


@router.get(
    "/{profile_id}/notifications/settings",
    response_model=NotificationRules,
    summary="Get profile notification rules",
)
async def get_notifications_settings(
    profile_id: int,
    _: Annotated[AccountMember | None, Depends(require_profile_viewer)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NotificationRules:
    rules = await NotifyService(WebsocketPusher(ws_manager), db).get_rules(profile_id)
    return NotificationRules.model_validate(rules)


@router.put(
    "/{profile_id}/notifications/settings",
    response_model=NotificationRules,
    summary="Update profile notification rules",
)
async def put_notifications_settings(
    profile_id: int,
    rules: NotificationRules,
    _: Annotated[AccountMember | None, Depends(require_profile_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NotificationRules:
    validate_notification_rules(rules)
    data = await NotifyService(WebsocketPusher(ws_manager), db).set_rules(profile_id, rules)
    return NotificationRules.model_validate(data)
