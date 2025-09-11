from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only

from app.core.log_filters import user_id_var
from app.core.preview import PreviewContext, get_preview_context
from app.core.security import verify_access_token
from app.domains.moderation.infrastructure.models.moderation_models import (
    UserRestriction,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.security import bearer_scheme
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TenantContext:
    """Resolved tenant context for request handling.

    Canonical identifier name is ``tenant_id``. For backward compatibility,
    we also accept ``workspace_id`` (deprecated) via query/path params.
    """

    tenant_id: UUID


def _parse_uuid_maybe(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except Exception:
        return None


async def get_tenant_id(
    request: Request,
    tenant_id: UUID | None = Query(default=None),
    workspace_id: UUID | None = Query(default=None),
) -> UUID:
    """Resolve tenant id from query or path params.

    Preference order:
    1) ``tenant_id`` query param
    2) ``workspace_id`` query param (deprecated; logs a warning)
    3) ``tenant_id`` in path params
    4) ``workspace_id``/``account_id`` in path params (deprecated)
    Raises 422 if nothing found.
    """

    if tenant_id is not None:
        return tenant_id
    if workspace_id is not None:
        logger.warning("Deprecated param workspace_id used; prefer tenant_id")
        return workspace_id
    # Path params fallback
    p = request.path_params or {}
    p_tenant = _parse_uuid_maybe(p.get("tenant_id"))
    if p_tenant is not None:
        return p_tenant
    p_workspace = _parse_uuid_maybe(p.get("workspace_id") or p.get("account_id"))
    if p_workspace is not None:
        logger.warning("Deprecated path param workspace_id/account_id used; prefer tenant_id")
        return p_workspace
    raise HTTPException(status_code=422, detail="tenant_id is required")


async def get_tenant_id_optional(
    request: Request,
    tenant_id: UUID | None = Query(default=None),
    workspace_id: UUID | None = Query(default=None),
) -> UUID | None:
    """Optional tenant resolver. Returns None when not provided.

    Accepts deprecated ``workspace_id`` for compatibility.
    """

    if tenant_id is not None:
        return tenant_id
    if workspace_id is not None:
        logger.warning("Deprecated param workspace_id used; prefer tenant_id")
        return workspace_id
    p = request.path_params or {}
    return _parse_uuid_maybe(
        p.get("tenant_id")
        or p.get("workspace_id")
        or p.get("account_id")
    )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    preview: Annotated[PreviewContext, Depends(get_preview_context)],
) -> User:
    # Приоритетно берем Bearer из Security-схемы Swagger; если нет — cookie
    token: str | None = None
    if credentials is not None and credentials.credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")
    user_id_str = verify_access_token(token) if token else None
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        user_id = UUID(user_id_str)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from err
    # Выбираем только безопасные колонки,
    # чтобы не падать на отсутствующих (например, premium_until)
    now = preview.now if preview and preview.now else datetime.utcnow()
    result = await db.execute(
        select(User, UserRestriction.type)
        .options(
            load_only(
                User.id,
                User.created_at,
                User.email,
                User.password_hash,
                User.wallet_address,
                User.is_active,
                User.username,
                User.bio,
                User.avatar_url,
                User.role,
                User.deleted_at,
            )
        )
        .outerjoin(
            UserRestriction,
            (
                (UserRestriction.user_id == User.id)
                & (UserRestriction.type.in_(["ban", "post_restrict"]))
                & ((UserRestriction.expires_at.is_(None)) | (UserRestriction.expires_at > now))
            ),
        )
        .where(User.id == user_id)
    )
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=404, detail="User not found")
    user = rows[0][0]
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    restrictions = {r for _, r in rows if r}
    user.active_restrictions = restrictions
    request.state.user_id = str(user.id)
    user_id_var.set(str(user.id))
    if "ban" in restrictions:
        raise HTTPException(status_code=403, detail="User is banned")
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    preview: Annotated[PreviewContext, Depends(get_preview_context)],
) -> User | None:
    """Return current user if auth header/cookie present, otherwise None."""
    token: str | None = None
    if credentials is not None and credentials.credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")
    if not token:
        return None
    user_id_str = verify_access_token(token)
    if not user_id_str:
        return None
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None
    now = preview.now if preview and preview.now else datetime.utcnow()
    result = await db.execute(
        select(User, UserRestriction.type)
        .options(
            load_only(
                User.id,
                User.created_at,
                User.email,
                User.password_hash,
                User.wallet_address,
                User.is_active,
                User.username,
                User.bio,
                User.avatar_url,
                User.role,
                User.deleted_at,
            )
        )
        .outerjoin(
            UserRestriction,
            (
                (UserRestriction.user_id == User.id)
                & (UserRestriction.type.in_(["ban", "post_restrict"]))
                & ((UserRestriction.expires_at.is_(None)) | (UserRestriction.expires_at > now))
            ),
        )
        .where(User.id == user_id)
    )
    rows = result.all()
    if not rows:
        return None
    user = rows[0][0]
    if not user or not user.is_active or user.deleted_at is not None:
        return None
    restrictions = {r for _, r in rows if r}
    user.active_restrictions = restrictions
    request.state.user_id = str(user.id)
    user_id_var.set(str(user.id))
    if "ban" in restrictions:
        return None
    return user


async def require_premium(
    user: Annotated[User, Depends(get_current_user)],
    preview: Annotated[PreviewContext, Depends(get_preview_context)],
) -> User:
    if preview and preview.plan == "premium":
        return user
    now = preview.now if preview and preview.now else datetime.utcnow()
    if not user.is_premium or (user.premium_until and user.premium_until < now):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return user


"""Common authorization helpers and role hierarchy for API dependencies.

Roles have strict seniority: ``user < moderator < admin``.  Helpers below
leverage this ranking to provide unified access checks across the API.
"""

role_order = {"user": 0, "support": 1, "moderator": 2, "admin": 3}


def require_role(min_role: str = "moderator"):
    async def _require_role(user: Annotated[User, Depends(get_current_user)]) -> User:
        if role_order.get(user.role, 0) < role_order[min_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _require_role


def assert_owner_or_role(owner_id: UUID, min_role: str, current_user: User) -> None:
    """Allow action if ``current_user`` owns the entity or has ``min_role``.

    Args:
        owner_id: Identifier of the entity owner.
        min_role: Minimal role required when user is not the owner.
        current_user: Authenticated user performing the action.
    """
    if current_user.id != owner_id and role_order.get(current_user.role, 0) < role_order[min_role]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def assert_seniority_over(target_user: User, current_user: User) -> None:
    """Ensure ``current_user`` is strictly senior to ``target_user``.

    Raises ``HTTPException`` with status 403 if the check fails.
    """
    if role_order.get(current_user.role, 0) <= role_order.get(target_user.role, 0):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


async def ensure_can_post(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if "post_restrict" in getattr(user, "active_restrictions", set()):
        raise HTTPException(status_code=403, detail="Posting restricted")
    return user


# Admin-only dependency for admin routes
admin_required = require_role("admin")
