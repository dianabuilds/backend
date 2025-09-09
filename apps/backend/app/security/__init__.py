from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains.moderation.infrastructure.models.moderation_models import (
    UserRestriction,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db

from .exceptions import (
    AuthRequiredError,
    ForbiddenError,
    InvalidTokenError,
    TokenExpiredError,
)
from .passwords import hash_password, verify_password

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


def verify_jwt(token: str) -> dict[str, Any]:
    key = settings.jwt.public_key or settings.jwt.secret
    try:
        return jwt.decode(
            token,
            key,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,
            issuer=settings.jwt.issuer,
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
            or_(
                UserRestriction.expires_at.is_(None),
                UserRestriction.expires_at > datetime.utcnow(),
            ),
        )
    )
    if result.scalars().first():
        raise ForbiddenError(user_id=str(user.id), role=user.role)
    return user


def create_preview_token(
    preview_session_id: str,
    ttl: int | None = None,
) -> str:
    payload = {
        "preview_session_id": preview_session_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=ttl or settings.jwt.expiration),
    }
    return jwt.encode(payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)


def verify_preview_token(token: str) -> dict[str, Any]:
    try:
        data = jwt.decode(
            token,
            settings.jwt.secret,
            algorithms=[settings.jwt.algorithm],
            leeway=settings.jwt.leeway,
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc
    if "preview_session_id" not in data:
        raise InvalidTokenError()
    return data


def require_admin_role(allowed_roles: set[str] | None = None):
    allowed = allowed_roles or set(settings.security.admin_roles)

    async def dependency(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Security(bearer_scheme)  # noqa: B008
        ] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
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


def require_admin_or_preview_token(allowed_roles: set[str] | None = None):
    admin_dep = require_admin_role(allowed_roles)

    async def dependency(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Security(bearer_scheme)  # noqa: B008
        ] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
    ):
        token = request.query_params.get("token") or request.headers.get("X-Preview-Token")
        if token:
            data = verify_preview_token(token)
            request.state.preview_token = data
            return None
        return await admin_dep(request, credentials, db)

    return dependency


async def auth_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)  # noqa: B008
    ] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
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


from fastapi import HTTPException


# Profile-centric stubs retained for compatibility with legacy dependencies.
async def require_ws_owner(*, scope_id=None, user, db):  # type: ignore[no-untyped-def]
    if getattr(user, "role", None) in {"admin"}:
        return SimpleNamespace(role="admin")  # type: ignore[name-defined]
    return SimpleNamespace(role="owner")  # type: ignore[name-defined]


async def require_ws_editor(*, scope_id=None, user, db):  # type: ignore[no-untyped-def]
    if getattr(user, "role", None) in {"admin"}:
        return SimpleNamespace(role="admin")  # type: ignore[name-defined]
    return SimpleNamespace(role="editor")  # type: ignore[name-defined]


async def require_ws_viewer(*, scope_id=None, user, db):  # type: ignore[no-untyped-def]
    if getattr(user, "role", None) in {"admin"}:
        return SimpleNamespace(role="admin")  # type: ignore[name-defined]
    return SimpleNamespace(role="viewer")  # type: ignore[name-defined]


async def require_ws_guest(*, scope_id=None, user, db):  # type: ignore[no-untyped-def]
    # Any authenticated user is a guest in profile mode
    if getattr(user, "id", None) is None:
        raise HTTPException(status_code=403, detail="Forbidden")  # type: ignore[arg-type]
    return SimpleNamespace(role="guest")  # type: ignore[name-defined]

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
    "create_preview_token",
    "verify_preview_token",
    "require_admin_or_preview_token",
    "auth_user",
    "hash_password",
    "verify_password",
    "require_ws_editor",
    "require_ws_owner",
    "require_ws_viewer",
    "require_ws_guest",
    "bearer_scheme",
    "ADMIN_AUTH_RESPONSES",
    "AuthRequiredError",
    "InvalidTokenError",
    "TokenExpiredError",
    "ForbiddenError",
]
