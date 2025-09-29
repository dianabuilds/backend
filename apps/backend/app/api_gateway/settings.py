from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.iam.adapters.credentials_sql import SQLCredentialsAdapter
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from domains.platform.notifications.adapters.matrix_sql import SQLNotificationMatrixRepo
from domains.platform.notifications.adapters.repo_sql import (
    SQLNotificationPreferenceRepo,
)
from domains.platform.notifications.application.preference_service import (
    PreferenceService,
)
from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine
from packages.core.errors import ApiError
from packages.core.settings_contract import (
    assert_if_match,
    attach_settings_schema,
    compute_etag,
    set_etag,
)

from .idempotency import IDEMPOTENCY_HEADER, require_idempotency_key
from .routers import get_container

SETTINGS_SCHEMA_TAG = "settings"


router = APIRouter(prefix="/v1/settings", tags=[SETTINGS_SCHEMA_TAG])
me_router = APIRouter(prefix="/v1/me/settings", tags=[SETTINGS_SCHEMA_TAG])

_FEATURE_SLUGS = {
    "notifications_email": "notifications.email",
    "notifications_digest": "notifications.digest",
    "security_session_alerts": "security.session.alerts",
    "billing_contracts": "billing.contracts",
}


class ProfileUpdatePayload(BaseModel):
    username: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    avatar_url: str | None = Field(default=None)


class EmailChangePayload(BaseModel):
    email: str


class EmailConfirmPayload(BaseModel):
    token: str


class WalletBindPayload(BaseModel):
    address: str
    chain_id: str | None = None
    signature: str | None = None


class NotificationPreferencesPayload(BaseModel):
    preferences: dict[str, Any]


class SessionTerminatePayload(BaseModel):
    reason: str | None = Field(default=None, max_length=256)


class SessionTerminateOthersPayload(BaseModel):
    password: str = Field(min_length=1)
    keep_session_id: str | None = None
    reason: str | None = Field(default=None, max_length=256)


async def _maybe_current_user(req: Request) -> dict[str, Any] | None:
    try:
        return await get_current_user(req)
    except HTTPException:
        return None
    except Exception:
        return None


def _subject_from_claims(claims: dict | None, fallback_user_id: str) -> dict[str, str]:
    subject: dict[str, str] = {"user_id": fallback_user_id}
    if not claims:
        return subject
    if claims.get("sub"):
        subject["user_id"] = str(claims.get("sub"))
    if claims.get("role"):
        subject["role"] = str(claims.get("role"))
    return subject


def _require_user_id(claims: dict[str, Any] | None) -> str:
    if claims and claims.get("sub"):
        return str(claims.get("sub"))
    raise ApiError(
        code="E_UNAUTHENTICATED",
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Authentication required",
    ) from None


def _profile_payload(response: Response, profile: dict[str, Any]) -> dict[str, Any]:
    etag = compute_etag(profile)
    set_etag(response, etag)
    payload = {"profile": profile}
    attach_settings_schema(payload, response)
    return payload


def _settings_payload(response: Response, key: str, value: Any) -> dict[str, Any]:
    etag = compute_etag(value)
    set_etag(response, etag)
    payload = {key: value}
    attach_settings_schema(payload, response)
    return payload


_PROFILE_ERROR_MAP: dict[str, tuple[int, str, str]] = {
    "profile_not_found": (
        status.HTTP_404_NOT_FOUND,
        "E_PROFILE_NOT_FOUND",
        "Profile not found",
    ),
    "invalid_username": (
        status.HTTP_400_BAD_REQUEST,
        "E_INVALID_USERNAME",
        "Username is invalid",
    ),
    "username_required": (
        status.HTTP_400_BAD_REQUEST,
        "E_USERNAME_REQUIRED",
        "Username is required",
    ),
    "username_taken": (
        status.HTTP_409_CONFLICT,
        "E_USERNAME_TAKEN",
        "Username already taken",
    ),
    "username_rate_limited": (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "E_USERNAME_RATE_LIMITED",
        "Username was changed recently",
    ),
    "invalid_bio": (
        status.HTTP_400_BAD_REQUEST,
        "E_INVALID_BIO",
        "Bio must be a string",
    ),
    "bio_too_long": (
        status.HTTP_400_BAD_REQUEST,
        "E_BIO_TOO_LONG",
        "Bio is too long",
    ),
    "invalid_avatar": (
        status.HTTP_400_BAD_REQUEST,
        "E_INVALID_AVATAR",
        "Avatar URL must be a string",
    ),
    "avatar_too_long": (
        status.HTTP_400_BAD_REQUEST,
        "E_AVATAR_TOO_LONG",
        "Avatar URL is too long",
    ),
    "invalid_email": (
        status.HTTP_400_BAD_REQUEST,
        "E_INVALID_EMAIL",
        "Email is invalid",
    ),
    "email_rate_limited": (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "E_EMAIL_RATE_LIMITED",
        "Email was changed recently",
    ),
    "email_same": (
        status.HTTP_400_BAD_REQUEST,
        "E_EMAIL_UNCHANGED",
        "Email already confirmed",
    ),
    "email_taken": (
        status.HTTP_409_CONFLICT,
        "E_EMAIL_TAKEN",
        "Email already in use",
    ),
    "email_change_not_found": (
        status.HTTP_404_NOT_FOUND,
        "E_EMAIL_CHANGE_NOT_FOUND",
        "Email change request not found",
    ),
    "wallet_required": (
        status.HTTP_400_BAD_REQUEST,
        "E_WALLET_REQUIRED",
        "Wallet address required",
    ),
    "wallet_taken": (
        status.HTTP_409_CONFLICT,
        "E_WALLET_TAKEN",
        "Wallet already bound",
    ),
}


def _raise_profile_error(error: ValueError) -> None:
    key = str(error)
    status_code, code, message = _PROFILE_ERROR_MAP.get(
        key,
        (status.HTTP_400_BAD_REQUEST, "E_PROFILE_INVALID", key),
    )
    raise ApiError(code=code, status_code=status_code, message=message) from None


def _dsn_from_settings(settings) -> str:
    try:
        dsn = to_async_dsn(settings.database_url)
    except Exception as exc:  # pragma: no cover - configuration issues
        raise RuntimeError("database_dsn_unavailable") from exc
    if not dsn:
        raise RuntimeError("database_dsn_unavailable")
    return str(dsn)


@lru_cache(maxsize=4)
def _engine_for_dsn(dsn: str) -> AsyncEngine:
    return get_async_engine("settings", url=dsn, pool_pre_ping=True, future=True)


@lru_cache(maxsize=4)
def _preference_service_for_dsn(dsn: str) -> PreferenceService:
    engine = _engine_for_dsn(dsn)
    preference_repo = SQLNotificationPreferenceRepo(engine)
    matrix_repo = SQLNotificationMatrixRepo(engine)
    return PreferenceService(matrix_repo=matrix_repo, preference_repo=preference_repo)


@lru_cache(maxsize=4)
def _credentials_adapter_for_dsn(dsn: str) -> SQLCredentialsAdapter:
    engine = _engine_for_dsn(dsn)
    return SQLCredentialsAdapter(engine)


async def _resolve_features(container, user_claims: dict[str, Any] | None) -> dict[str, bool]:
    svc = container.flags.service
    claims = user_claims or {}
    result: dict[str, bool] = {}
    for api_key, flag_slug in _FEATURE_SLUGS.items():
        try:
            result[api_key] = bool(await svc.evaluate(flag_slug, claims))
        except Exception:
            result[api_key] = False
    return result


async def _features_payload(
    request: Request,
    response: Response,
    claims: dict[str, Any] | None,
) -> dict[str, Any]:
    container = get_container(request)
    features = await _resolve_features(container, claims)
    payload = {"features": features, "idempotency_header": IDEMPOTENCY_HEADER}
    attach_settings_schema(payload, response)
    return payload


async def _billing_bundle(container, user_id: str) -> dict[str, Any]:
    svc = container.billing.service
    summary = await svc.get_summary_for_user(user_id)
    history = await svc.get_history_for_user(user_id)
    wallet = None
    try:
        profile = await container.profile_service.get_profile(user_id)
        wallet = profile.get("wallet")
    except ValueError:
        wallet = None
    return {"summary": summary, "history": history, "wallet": wallet}


def _get_preference_service(container) -> PreferenceService:
    svc = getattr(getattr(container, "notifications", object()), "preference_service", None)
    if svc is not None:
        return svc
    dsn = _dsn_from_settings(container.settings)
    return _preference_service_for_dsn(dsn)


def _get_credentials_adapter(container) -> SQLCredentialsAdapter:
    dsn = _dsn_from_settings(container.settings)
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
    user = None
    try:
        user = await container.users.service.get(user_id)
    except Exception:
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
        except Exception:
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


@router.get("/features")
async def settings_features(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    return await _features_payload(request, response, claims)


@me_router.get("/features")
async def me_settings_features(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    return await _features_payload(request, response, claims)


@router.get("/profile/{user_id}")
async def settings_profile_get(
    user_id: str,
    request: Request,
    response: Response,
    _admin: None = Depends(require_admin),
    claims=Depends(_maybe_current_user),
) -> dict[str, Any]:
    container = get_container(request)
    svc = container.profile_service
    try:
        profile = await svc.get_profile(user_id)
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, profile)


@router.put("/profile/{user_id}")
async def settings_profile_update(
    user_id: str,
    body: ProfileUpdatePayload,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None, alias="If-Match"),
    claims=Depends(_maybe_current_user),
    _admin: None = Depends(require_admin),
) -> dict[str, Any]:
    container = get_container(request)
    svc = container.profile_service
    try:
        current = await svc.get_profile(user_id)
    except ValueError as exc:
        _raise_profile_error(exc)
    assert_if_match(if_match, compute_etag(current))
    payload = body.model_dump(exclude_unset=True)
    fallback_actor = claims.get("sub") if claims and claims.get("sub") else user_id
    subject = _subject_from_claims(claims, str(fallback_actor))
    subject.setdefault("role", "admin")
    try:
        updated = await svc.update_profile(user_id, payload, subject=subject)
    except PermissionError:
        raise ApiError(
            code="E_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            message="Operation forbidden",
        ) from None
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, updated)


@me_router.get("/profile")
async def me_settings_profile_get(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = container.profile_service
    try:
        profile = await svc.get_profile(user_id)
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, profile)


@me_router.put("/profile")
async def me_settings_profile_update(
    body: ProfileUpdatePayload,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None, alias="If-Match"),
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = container.profile_service
    try:
        current = await svc.get_profile(user_id)
    except ValueError as exc:
        _raise_profile_error(exc)
    assert_if_match(if_match, compute_etag(current))
    payload = body.model_dump(exclude_unset=True)
    subject = _subject_from_claims(claims, user_id)
    try:
        updated = await svc.update_profile(user_id, payload, subject=subject)
    except PermissionError:
        raise ApiError(
            code="E_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            message="Operation forbidden",
        ) from None
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, updated)


@me_router.post(
    "/profile/email/request-change",
    dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
)
async def me_settings_email_request(
    payload: EmailChangePayload,
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = container.profile_service
    subject = _subject_from_claims(claims, user_id)
    try:
        result = await svc.request_email_change(user_id, payload.email, subject=subject)
    except PermissionError:
        raise ApiError(
            code="E_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            message="Operation forbidden",
        ) from None
    except ValueError as exc:
        _raise_profile_error(exc)
    attach_settings_schema(result, response)
    return result


@me_router.post(
    "/profile/email/confirm",
    dependencies=[Depends(csrf_protect)],
)
async def me_settings_email_confirm(
    payload: EmailConfirmPayload,
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = container.profile_service
    subject = _subject_from_claims(claims, user_id)
    try:
        updated = await svc.confirm_email_change(user_id, payload.token, subject=subject)
    except PermissionError:
        raise ApiError(
            code="E_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            message="Operation forbidden",
        ) from None
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, updated)


@me_router.post(
    "/profile/wallet",
    dependencies=[Depends(csrf_protect)],
)
async def me_settings_wallet_bind(
    payload: WalletBindPayload,
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = container.profile_service
    subject = _subject_from_claims(claims, user_id)
    try:
        updated = await svc.set_wallet(
            user_id,
            address=payload.address.strip(),
            chain_id=(payload.chain_id.strip() if payload.chain_id else None),
            signature=payload.signature,
            subject=subject,
        )
    except PermissionError:
        raise ApiError(
            code="E_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            message="Operation forbidden",
        ) from None
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, updated)


@me_router.delete(
    "/profile/wallet",
    dependencies=[Depends(csrf_protect)],
)
async def me_settings_wallet_unbind(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = container.profile_service
    subject = _subject_from_claims(claims, user_id)
    try:
        updated = await svc.clear_wallet(user_id, subject)
    except PermissionError:
        raise ApiError(
            code="E_FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            message="Operation forbidden",
        ) from None
    except ValueError as exc:
        _raise_profile_error(exc)
    return _profile_payload(response, updated)


@router.get("/billing/{user_id}")
async def settings_billing_get(
    user_id: str,
    request: Request,
    response: Response,
    _admin: None = Depends(require_admin),
) -> dict[str, Any]:
    container = get_container(request)
    try:
        data = await _billing_bundle(container, user_id)
    except RuntimeError:
        raise ApiError(
            code="E_BILLING_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Billing backend unavailable",
        ) from None
    return _settings_payload(response, "billing", data)


@me_router.get("/billing")
async def me_settings_billing_get(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    try:
        data = await _billing_bundle(container, user_id)
    except RuntimeError:
        raise ApiError(
            code="E_BILLING_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Billing backend unavailable",
        ) from None
    return _settings_payload(response, "billing", data)


@router.get("/notifications/{user_id}/preferences")
async def settings_notifications_get(
    user_id: str,
    request: Request,
    response: Response,
    _admin: None = Depends(require_admin),
) -> dict[str, Any]:
    container = get_container(request)
    try:
        prefs = await _get_preference_service(container).get_preferences(user_id)
    except RuntimeError:
        raise ApiError(
            code="E_NOTIFICATIONS_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Notifications backend unavailable",
        ) from None
    return _settings_payload(response, "preferences", prefs)


@router.put(
    "/notifications/{user_id}/preferences",
    dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
)
async def settings_notifications_put(
    user_id: str,
    body: NotificationPreferencesPayload,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None, alias="If-Match"),
    _admin: None = Depends(require_admin),
) -> dict[str, Any]:
    container = get_container(request)
    svc = _get_preference_service(container)
    try:
        current = await svc.get_preferences(user_id)
    except RuntimeError:
        raise ApiError(
            code="E_NOTIFICATIONS_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Notifications backend unavailable",
        ) from None
    assert_if_match(if_match, compute_etag(current))
    await svc.set_preferences(user_id, body.preferences)
    updated = await svc.get_preferences(user_id)
    payload = _settings_payload(response, "preferences", updated)
    try:
        await container.audit.service.log(
            actor_id=None,
            action="notifications.preferences.updated",
            resource_type="user",
            resource_id=user_id,
            after=updated,
        )
    except Exception:
        pass
    return payload


@me_router.get("/notifications/preferences")
async def me_settings_notifications_get(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = _get_preference_service(container)
    context = claims or {"sub": user_id}
    try:
        overview = await svc.get_preferences_overview(user_id, context=context)
    except RuntimeError:
        raise ApiError(
            code="E_NOTIFICATIONS_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Notifications backend unavailable",
        ) from None
    return _settings_payload(response, "overview", overview)


@me_router.put(
    "/notifications/preferences",
    dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
)
async def me_settings_notifications_put(
    body: NotificationPreferencesPayload,
    request: Request,
    response: Response,
    if_match: str | None = Header(default=None, alias="If-Match"),
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    svc = _get_preference_service(container)
    context = claims or {"sub": user_id}
    try:
        current = await svc.get_preferences_overview(user_id, context=context)
    except RuntimeError:
        raise ApiError(
            code="E_NOTIFICATIONS_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Notifications backend unavailable",
        ) from None
    assert_if_match(if_match, compute_etag(current))
    request_id = request.headers.get(IDEMPOTENCY_HEADER)
    await svc.set_preferences(
        user_id,
        body.preferences,
        actor_id=user_id,
        source="user",
        context=context,
        request_id=request_id,
    )
    updated = await svc.get_preferences_overview(user_id, context=context)
    payload = _settings_payload(response, "overview", updated)
    try:
        await container.audit.service.log(
            actor_id=user_id,
            action="notifications.preferences.updated",
            resource_type="user",
            resource_id=user_id,
            after=updated,
        )
    except Exception:
        pass
    return payload


@router.get("/security/{user_id}/sessions")
async def settings_security_sessions_get(
    user_id: str,
    request: Request,
    response: Response,
    _admin: None = Depends(require_admin),
) -> dict[str, Any]:
    container = get_container(request)
    try:
        engine = _engine_for_dsn(_dsn_from_settings(container.settings))
    except RuntimeError:
        raise ApiError(
            code="E_SECURITY_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Security backend unavailable",
        ) from None
    sessions = await _list_sessions(engine, user_id)
    return _settings_payload(response, "sessions", sessions)


@me_router.get("/security/sessions")
async def me_settings_security_sessions_get(
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    container = get_container(request)
    try:
        engine = _engine_for_dsn(_dsn_from_settings(container.settings))
    except RuntimeError:
        raise ApiError(
            code="E_SECURITY_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Security backend unavailable",
        ) from None
    sessions = await _list_sessions(engine, user_id)
    return _settings_payload(response, "sessions", sessions)


@me_router.post(
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
    user_id = _require_user_id(claims)
    sid = _normalize_uuid(session_id, field="session")
    container = get_container(request)
    try:
        engine = _engine_for_dsn(_dsn_from_settings(container.settings))
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
    except Exception:
        pass
    return _settings_payload(response, "sessions", sessions)


@me_router.post(
    "/security/sessions/terminate-others",
    dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
)
async def me_settings_security_terminate_others(
    payload: SessionTerminateOthersPayload,
    request: Request,
    response: Response,
    claims=Depends(get_current_user),
) -> dict[str, Any]:
    user_id = _require_user_id(claims)
    keep_sid = (
        _normalize_uuid(payload.keep_session_id, field="session")
        if payload.keep_session_id
        else None
    )
    container = get_container(request)
    await _verify_password(container, user_id, payload.password)
    try:
        engine = _engine_for_dsn(_dsn_from_settings(container.settings))
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
    except Exception:
        pass
    return _settings_payload(response, "sessions", sessions)


__all__ = ["router", "me_router", "SETTINGS_SCHEMA_TAG"]
