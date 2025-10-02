from __future__ import annotations

import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.iam.adapters.credentials_sql import SQLCredentialsAdapter
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from packages.core.errors import ApiError

from ..idempotency import require_idempotency_key
from ..routers import get_container
from .common import dsn_from_settings, engine_for_dsn, require_user_id, settings_payload

logger = logging.getLogger(__name__)


class SessionTerminatePayload(BaseModel):
    reason: str | None = Field(default=None, max_length=256)


class SessionTerminateOthersPayload(BaseModel):
    password: str = Field(min_length=1)
    keep_session_id: str | None = None
    reason: str | None = Field(default=None, max_length=256)


@lru_cache(maxsize=4)
def _credentials_adapter_for_dsn(dsn: str) -> SQLCredentialsAdapter:
    engine = engine_for_dsn(dsn)
    return SQLCredentialsAdapter(engine)


def _get_credentials_adapter(container) -> SQLCredentialsAdapter:
    dsn = dsn_from_settings(container.settings)
    return _credentials_adapter_for_dsn(dsn)


async def _verify_password(container, user_id: str, password: str) -> None:
    if not password:
        raise ApiError(
            code="E_PASSWORD_REQUIRED",
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Password is required",
        ) from None
    settings = container.settings
    if (
        settings.auth_bootstrap_user_id
        and str(settings.auth_bootstrap_user_id) == str(user_id)
        and settings.auth_bootstrap_password is not None
    ):
        if password == settings.auth_bootstrap_password:
            return
    try:
        user = await container.users.service.get(user_id)
    except Exception as exc:
        logger.exception("Failed to load user %s for password verification", user_id, exc_info=exc)
        user = None
    logins: list[str] = []
    if user:
        if user.username:
            logins.append(str(user.username))
        if user.email:
            logins.append(str(user.email))
    adapter = _get_credentials_adapter(container)
    for login in logins or [user_id]:
        try:
            identity = await adapter.authenticate(login, password)
        except Exception as exc:
            logger.exception("Credential lookup failed for login %s", login, exc_info=exc)
            continue
        if identity and str(identity.id) == str(user_id):
            return
    raise ApiError(
        code="E_INVALID_PASSWORD",
        status_code=status.HTTP_403_FORBIDDEN,
        message="Password verification failed",
    ) from None


def _normalize_uuid(value: str, *, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except Exception as exc:
        raise ApiError(
            code="E_INVALID_IDENTIFIER",
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Invalid {field}",
        ) from exc


async def _list_sessions(engine: AsyncEngine, user_id: str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            id::text AS id,
            user_agent,
            ip,
            created_at,
            last_used_at,
            expires_at,
            refresh_expires_at,
            revoked_at,
            device_id::text AS device_id,
            platform_fingerprint,
            terminated_by::text AS terminated_by,
            terminated_reason
        FROM user_sessions
        WHERE user_id = cast(:uid as uuid)
        ORDER BY created_at DESC
        """
    )
    async with engine.begin() as conn:
        rows = (await conn.execute(query, {"uid": user_id})).mappings().all()
    now = datetime.now(UTC)
    sessions: list[dict[str, Any]] = []
    for row in rows:
        revoked_at = row.get("revoked_at")
        expires_at = row.get("expires_at")
        active = revoked_at is None and (expires_at is None or expires_at > now)
        sessions.append(
            {
                "id": row.get("id"),
                "ip": row.get("ip"),
                "user_agent": row.get("user_agent"),
                "created_at": row.get("created_at"),
                "last_used_at": row.get("last_used_at"),
                "expires_at": expires_at,
                "refresh_expires_at": row.get("refresh_expires_at"),
                "revoked_at": revoked_at,
                "device_id": row.get("device_id"),
                "platform_fingerprint": row.get("platform_fingerprint"),
                "terminated_by": row.get("terminated_by"),
                "terminated_reason": row.get("terminated_reason"),
                "active": active,
            }
        )
    return sessions


async def _terminate_session(
    engine: AsyncEngine,
    *,
    user_id: str,
    session_id: str,
    actor_id: str | None,
    reason: str | None,
) -> bool:
    query = text(
        """
        UPDATE user_sessions
        SET revoked_at = now(),
            terminated_by = CASE WHEN :actor_id IS NULL THEN terminated_by ELSE cast(:actor_id as uuid) END,
            terminated_reason = :reason
        WHERE id = cast(:sid as uuid)
          AND user_id = cast(:uid as uuid)
          AND revoked_at IS NULL
        RETURNING id
        """
    )
    async with engine.begin() as conn:
        result = await conn.execute(
            query,
            {
                "sid": session_id,
                "uid": user_id,
                "actor_id": actor_id,
                "reason": reason,
            },
        )
        row = result.first()
    return bool(row)


async def _terminate_other_sessions(
    engine: AsyncEngine,
    *,
    user_id: str,
    keep_session_id: str | None,
    actor_id: str | None,
    reason: str | None,
) -> list[str]:
    query = text(
        """
        UPDATE user_sessions
        SET revoked_at = now(),
            terminated_by = CASE WHEN :actor_id IS NULL THEN terminated_by ELSE cast(:actor_id as uuid) END,
            terminated_reason = :reason
        WHERE user_id = cast(:uid as uuid)
          AND revoked_at IS NULL
          AND (
            :keep_sid IS NULL OR id <> cast(:keep_sid as uuid)
          )
        RETURNING id::text AS id
        """
    )
    async with engine.begin() as conn:
        rows = (
            (
                await conn.execute(
                    query,
                    {
                        "uid": user_id,
                        "keep_sid": keep_session_id,
                        "actor_id": actor_id,
                        "reason": reason,
                    },
                )
            )
            .mappings()
            .all()
        )
    return [str(r["id"]) for r in rows]


def register(admin_router: APIRouter, personal_router: APIRouter) -> None:
    @admin_router.get("/security/{user_id}/sessions")
    async def settings_security_sessions_get(
        user_id: str,
        request: Request,
        response: Response,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(request)
        try:
            engine = engine_for_dsn(dsn_from_settings(container.settings))
        except RuntimeError:
            raise ApiError(
                code="E_SECURITY_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Security backend unavailable",
            ) from None
        sessions = await _list_sessions(engine, user_id)
        return settings_payload(response, "sessions", sessions)

    @personal_router.get("/security/sessions")
    async def me_settings_security_sessions_get(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        try:
            engine = engine_for_dsn(dsn_from_settings(container.settings))
        except RuntimeError:
            raise ApiError(
                code="E_SECURITY_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Security backend unavailable",
            ) from None
        sessions = await _list_sessions(engine, user_id)
        return settings_payload(response, "sessions", sessions)

    @personal_router.post(
        "/security/sessions/{session_id}/terminate",
        dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
    )
    async def me_settings_security_terminate_session(
        session_id: str,
        payload: SessionTerminatePayload,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        sid = _normalize_uuid(session_id, field="session")
        container = get_container(request)
        try:
            engine = engine_for_dsn(dsn_from_settings(container.settings))
        except RuntimeError:
            raise ApiError(
                code="E_SECURITY_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Security backend unavailable",
            ) from None
        actor_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        ok = await _terminate_session(
            engine,
            user_id=user_id,
            session_id=sid,
            actor_id=actor_id,
            reason=payload.reason,
        )
        if not ok:
            raise ApiError(
                code="E_SESSION_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
                message="Session not found",
            ) from None
        sessions = await _list_sessions(engine, user_id)
        try:
            await container.audit.service.log(
                actor_id=user_id,
                action="security.session.terminated",
                resource_type="session",
                resource_id=sid,
                reason=payload.reason,
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as exc:
            logger.exception("Failed to audit session termination", exc_info=exc)
        return settings_payload(response, "sessions", sessions)

    @personal_router.post(
        "/security/sessions/terminate-others",
        dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
    )
    async def me_settings_security_terminate_others(
        payload: SessionTerminateOthersPayload,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        keep_sid = (
            _normalize_uuid(payload.keep_session_id, field="session")
            if payload.keep_session_id
            else None
        )
        container = get_container(request)
        await _verify_password(container, user_id, payload.password)
        try:
            engine = engine_for_dsn(dsn_from_settings(container.settings))
        except RuntimeError:
            raise ApiError(
                code="E_SECURITY_UNAVAILABLE",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Security backend unavailable",
            ) from None
        actor_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        terminated = await _terminate_other_sessions(
            engine,
            user_id=user_id,
            keep_session_id=keep_sid,
            actor_id=actor_id,
            reason=payload.reason,
        )
        if not terminated:
            raise ApiError(
                code="E_NO_SESSIONS_TERMINATED",
                status_code=status.HTTP_404_NOT_FOUND,
                message="No sessions to terminate",
            ) from None
        sessions = await _list_sessions(engine, user_id)
        try:
            await container.audit.service.log(
                actor_id=user_id,
                action="security.session.mass_logout",
                resource_type="user",
                resource_id=user_id,
                reason=payload.reason,
                extra={"terminated": terminated, "keep_session_id": keep_sid},
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as exc:
            logger.exception("Failed to audit mass session termination", exc_info=exc)
        return settings_payload(response, "sessions", sessions)


__all__ = [
    "SessionTerminateOthersPayload",
    "SessionTerminatePayload",
    "register",
]
