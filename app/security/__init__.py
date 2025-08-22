from __future__ import annotations

from datetime import datetime
from typing import Any, Set
from uuid import UUID

import jwt
from fastapi import Depends, Request, Security, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.db.session import get_db
from app.domains.users.infrastructure.models.user import User
from app.domains.moderation.infrastructure.models.moderation_models import UserRestriction

from .exceptions import (
    AuthRequiredError,
    InvalidTokenError,
    TokenExpiredError,
    ForbiddenError,
)

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


def verify_jwt(token: str) -> dict[str, Any]:
    key = settings.jwt.public_key or settings.jwt.secret
    try:
        return jwt.decode(
            token,
            key,
            algorithms=[settings.jwt.algorithm],
            leeway=settings.jwt.leeway,
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc


async def get_current_user(token: str, db: AsyncSession) -> User:
    payload = verify_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError()
    try:
        user_id = UUID(str(sub))
    except ValueError as exc:
        raise InvalidTokenError() from exc
    user = await db.get(User, user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise ForbiddenError()
    result = await db.execute(
        select(UserRestriction).where(
            UserRestriction.user_id == user.id,
            UserRestriction.type == "ban",
            (UserRestriction.expires_at == None)
            | (UserRestriction.expires_at > datetime.utcnow()),
        )
    )
    if result.scalars().first():
        raise ForbiddenError(user_id=str(user.id), role=user.role)
    return user


def require_admin_role(allowed_roles: Set[str] | None = None):
    allowed = allowed_roles or set(settings.security.admin_roles)

    async def dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # Приоритет: Bearer из заголовка; если его нет — берём access_token из cookie.
        token: str | None = None
        if credentials is not None and credentials.credentials:
            token = credentials.credentials
        else:
            token = request.cookies.get("access_token")

        if not token:
            raise AuthRequiredError()

        user = await get_current_user(token, db)
        if user.role not in allowed:
            raise ForbiddenError(user_id=str(user.id), role=user.role)
        request.state.user_id = str(user.id)
        return user

    return dependency


async def auth_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token: str | None = None
    if credentials is not None and credentials.credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise AuthRequiredError()

    user = await get_current_user(token, db)
    request.state.user_id = str(user.id)
    return user


async def require_ws_editor(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
):
    from app.domains.workspaces.infrastructure.dao import WorkspaceMemberDAO

    m = await WorkspaceMemberDAO.get(
        db, workspace_id=workspace_id, user_id=user.id
    )
    if not (
        user.role == "admin" or (m and m.role in ("owner", "editor"))
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return m


ADMIN_AUTH_RESPONSES = {
    401: {
        "description": "Unauthorized",
        "nodes": {
            "application/json": {
                "examples": {
                    "missing": {
                        "summary": "Missing token",
                        "value": {
                            "error": {
                                "code": "AUTH_REQUIRED",
                                "message": "Authorization required",
                            }
                        },
                    },
                    "invalid": {
                        "summary": "Invalid token",
                        "value": {
                            "error": {
                                "code": "INVALID_TOKEN",
                                "message": "Invalid authentication token",
                            }
                        },
                    },
                    "expired": {
                        "summary": "Expired token",
                        "value": {
                            "error": {
                                "code": "TOKEN_EXPIRED",
                                "message": "Token has expired",
                            }
                        },
                    },
                }
            }
        },
    },
    403: {
        "description": "Forbidden",
        "nodes": {
            "application/json": {
                "example": {"error": {"code": "FORBIDDEN", "message": "Forbidden"}}
            }
        },
    },
}

__all__ = [
    "verify_jwt",
    "get_current_user",
    "require_admin_role",
    "auth_user",
    "require_ws_editor",
    "bearer_scheme",
    "ADMIN_AUTH_RESPONSES",
    "AuthRequiredError",
    "InvalidTokenError",
    "TokenExpiredError",
    "ForbiddenError",
]
