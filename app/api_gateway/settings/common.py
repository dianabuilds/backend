from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.iam.security import get_current_user
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine
from packages.core.errors import ApiError
from packages.core.settings_contract import (
    attach_settings_schema,
    compute_etag,
    set_etag,
)

SETTINGS_SCHEMA_TAG = "settings"

logger = logging.getLogger(__name__)


async def maybe_current_user(request: Request) -> dict[str, Any] | None:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
    except Exception as exc:
        logger.exception("Failed to resolve current user claims", exc_info=exc)
        return None


def subject_from_claims(claims: dict | None, fallback_user_id: str) -> dict[str, str]:
    subject: dict[str, str] = {"user_id": fallback_user_id}
    if not claims:
        return subject
    if claims.get("sub"):
        subject["user_id"] = str(claims["sub"])
    if claims.get("role"):
        subject["role"] = str(claims["role"])
    return subject


def require_user_id(claims: dict[str, Any] | None) -> str:
    if claims and claims.get("sub"):
        return str(claims["sub"])
    raise ApiError(
        code="E_UNAUTHENTICATED",
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Authentication required",
    ) from None


def profile_payload(response: Response, profile: dict[str, Any]) -> dict[str, Any]:
    etag = compute_etag(profile)
    set_etag(response, etag)
    payload = {"profile": profile}
    attach_settings_schema(payload, response)
    return payload


def settings_payload(response: Response, key: str, value: Any) -> dict[str, Any]:
    etag = compute_etag(value)
    set_etag(response, etag)
    payload = {key: value}
    attach_settings_schema(payload, response)
    return payload


def dsn_from_settings(settings: Any) -> str:
    try:
        dsn = to_async_dsn(settings.database_url)
    except Exception as exc:
        logger.exception("Failed to derive async DSN from settings")
        raise RuntimeError("database_dsn_unavailable") from exc
    if not dsn:
        raise RuntimeError("database_dsn_unavailable")
    return str(dsn)


@lru_cache(maxsize=4)
def engine_for_dsn(dsn: str) -> AsyncEngine:
    return get_async_engine("settings", url=dsn, pool_pre_ping=True, future=True)


__all__ = [
    "SETTINGS_SCHEMA_TAG",
    "dsn_from_settings",
    "engine_for_dsn",
    "maybe_current_user",
    "profile_payload",
    "require_user_id",
    "settings_payload",
    "subject_from_claims",
]
