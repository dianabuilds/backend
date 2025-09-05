from __future__ import annotations

from collections.abc import Mapping

# ruff: noqa: B008
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jsonschema import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.application.service import (
    AccountService,
    require_account_editor,
    require_account_owner,
    require_account_viewer,
)
from app.domains.accounts.infrastructure.dao import AccountDAO
from app.domains.accounts.infrastructure.models import AccountMember
from app.domains.ai.infrastructure.repositories.usage_repository import (
    AIUsageRepository,
)
from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.repositories import (
    notification_repository,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.notifications.validation import validate_notification_rules
from app.domains.users.infrastructure.models.user import User
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
)
from app.schemas.notification import NotificationType
from app.schemas.notification_rules import NotificationRules
from app.security import ADMIN_AUTH_RESPONSES, auth_user

router = APIRouter(
    prefix="/admin/accounts",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("", response_model=AccountOut, status_code=201, summary="Create account")
async def create_account(
    data: AccountIn,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountOut:
    account = await AccountService.create(db, data=data, owner=user)
    return account


@router.get("", response_model=AccountCursorPage, summary="List accounts")
async def list_accounts(
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


@router.get("/{account_id}", response_model=AccountOut, summary="Get account")
async def get_account(
    account_id: UUID,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountOut:
    return await AccountService.get_for_user(db, account_id, user)


@router.patch("/{account_id}", response_model=AccountOut, summary="Update account")
async def update_account(
    account_id: UUID,
    data: AccountUpdate,
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountOut:
    return await AccountService.update(db, account_id, data)


@router.delete("/{account_id}", status_code=204, summary="Delete account")
async def delete_account(
    account_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await AccountService.delete(db, account_id)
    return Response(status_code=204)


@router.post(
    "/{account_id}/members",
    response_model=AccountMemberOut,
    status_code=201,
    summary="Add account member",
)
async def add_member(
    account_id: UUID,
    data: AccountMemberIn,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMemberOut:
    return await AccountService.add_member(db, account_id, data)


@router.patch(
    "/{account_id}/members/{user_id}",
    response_model=AccountMemberOut,
    summary="Update account member",
)
async def update_member(
    account_id: UUID,
    user_id: UUID,
    data: AccountMemberIn,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AccountMemberOut:
    if data.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    return await AccountService.update_member(db, account_id, user_id, data.role)


@router.delete(
    "/{account_id}/members/{user_id}",
    status_code=204,
    summary="Remove account member",
)
async def remove_member(
    account_id: UUID,
    user_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await AccountService.remove_member(db, account_id, user_id)
    return Response(status_code=204)


@router.get(
    "/{account_id}/members",
    response_model=list[AccountMemberOut],
    summary="List account members",
)
async def list_members(
    account_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[AccountMemberOut]:
    return await AccountService.list_members(db, account_id)


@router.get(
    "/{account_id}/settings/ai-presets",
    response_model=dict[str, Any],
    summary="Get account AI presets",
)
async def get_ai_presets(
    account_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    return await AccountService.get_ai_presets(db, account_id)


@router.put(
    "/{account_id}/settings/ai-presets",
    response_model=dict[str, Any],
    summary="Update account AI presets",
)
async def put_ai_presets(
    account_id: UUID,
    presets: dict[str, Any],
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    account = await AccountDAO.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    try:
        from app.domains.ai.validation import validate_ai_presets

        validate_ai_presets(presets)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    settings = AccountSettings.model_validate(account.settings_json)
    settings.ai_presets = presets
    account.settings_json = settings.model_dump()
    await db.commit()
    await db.refresh(account)
    return settings.ai_presets


@router.get(
    "/{account_id}/settings/notifications",
    response_model=NotificationRules,
    summary="Get account notification rules",
)
async def get_notifications(
    account_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NotificationRules:
    account = await AccountDAO.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    settings = AccountSettings.model_validate(account.settings_json)
    return settings.notifications


@router.put(
    "/{account_id}/settings/notifications",
    response_model=NotificationRules,
    summary="Update account notification rules",
)
async def put_notifications(
    account_id: UUID,
    rules: NotificationRules,
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NotificationRules:
    account = await AccountDAO.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    # Validate explicitly
    _ = validate_notification_rules(rules.model_dump())
    settings = AccountSettings.model_validate(account.settings_json)
    settings.notifications = rules
    account.settings_json = settings.model_dump()
    await db.commit()
    await db.refresh(account)
    return settings.notifications


@router.get(
    "/{account_id}/settings/limits",
    response_model=dict[str, int],
    summary="Get account limits",
)
async def get_limits(
    account_id: UUID,
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, int]:
    account = await AccountDAO.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    settings = AccountSettings.model_validate(account.settings_json)
    return settings.limits


@router.put(
    "/{account_id}/settings/limits",
    response_model=dict[str, int],
    summary="Update account limits",
)
async def put_limits(
    account_id: UUID,
    limits: dict[str, int],
    _: Annotated[AccountMember | None, Depends(require_account_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, int]:
    account = await AccountDAO.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    settings = AccountSettings.model_validate(account.settings_json)
    settings.limits = limits
    account.settings_json = settings.model_dump()
    await db.commit()
    await db.refresh(account)
    return settings.limits


@router.get(
    "/{account_id}/usage",
    summary="Get account AI usage",
)
async def get_account_usage(
    account_id: UUID,
    user: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[AccountMember | None, Depends(require_account_viewer)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    repo = AIUsageRepository(db)
    totals = await repo.account_totals(account_id)
    account = await AccountDAO.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    settings = AccountSettings.model_validate(account.settings_json)
    limit = int(settings.limits.get("ai_tokens", 0))
    tokens = int(totals["tokens"])
    progress = tokens / limit if limit else 0
    alert: str | None = None
    if limit:
        ratio = tokens / limit
        if ratio >= 1:
            alert = "quota_exceeded"
        elif ratio >= 0.8:
            alert = "quota_warning"
    if alert:
        try:
            notify = NotifyService(
                notification_repository.NotificationRepository(db),
                WebsocketPusher(ws_manager),
            )
            await notify.create_notification(
                account_id=account_id,
                user_id=user.id,
                title="AI quota alert",
                message=f"AI token usage {tokens}/{limit}",
                type=NotificationType.system,
            )
        except Exception:
            pass
    return {
        "account_id": account_id,
        "tokens": tokens,
        "cost": float(totals["cost"]),
        "limit": limit,
        "progress": progress,
        "alert": alert,
    }
