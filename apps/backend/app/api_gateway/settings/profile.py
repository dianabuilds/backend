from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Request, Response, status
from pydantic import BaseModel, Field

from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from packages.core.errors import ApiError
from packages.core.settings_contract import (
    assert_if_match,
    attach_settings_schema,
    compute_etag,
)

from ..idempotency import require_idempotency_key
from ..routers import get_container
from .common import (
    maybe_current_user,
    profile_payload,
    require_user_id,
    subject_from_claims,
)


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
    "email_same": (
        status.HTTP_400_BAD_REQUEST,
        "E_EMAIL_UNCHANGED",
        "Email already confirmed",
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
    "email_taken": (
        status.HTTP_409_CONFLICT,
        "E_EMAIL_TAKEN",
        "Email already in use",
    ),
    "email_rate_limited": (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "E_EMAIL_RATE_LIMITED",
        "Email change was requested recently",
    ),
    "email_token_invalid": (
        status.HTTP_400_BAD_REQUEST,
        "E_EMAIL_TOKEN_INVALID",
        "Email confirmation token is invalid",
    ),
    "wallet_invalid": (
        status.HTTP_400_BAD_REQUEST,
        "E_WALLET_INVALID",
        "Wallet address invalid",
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


def register(admin_router: APIRouter, personal_router: APIRouter) -> None:
    @admin_router.get("/profile/{user_id}")
    async def settings_profile_get(
        user_id: str,
        request: Request,
        response: Response,
        _admin: None = Depends(require_admin),
        claims=Depends(maybe_current_user),
    ) -> dict[str, Any]:
        container = get_container(request)
        svc = container.profile_service
        try:
            profile = await svc.get_profile(user_id)
        except ValueError as exc:
            _raise_profile_error(exc)
        return profile_payload(response, profile)

    @admin_router.put("/profile/{user_id}")
    async def settings_profile_update(
        user_id: str,
        body: ProfileUpdatePayload,
        request: Request,
        response: Response,
        if_match: str | None = Header(default=None, alias="If-Match"),
        claims=Depends(maybe_current_user),
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
        subject = subject_from_claims(claims, str(fallback_actor))
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
        return profile_payload(response, updated)

    @personal_router.get("/profile")
    async def me_settings_profile_get(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = container.profile_service
        try:
            profile = await svc.get_profile(user_id)
        except ValueError as exc:
            _raise_profile_error(exc)
        return profile_payload(response, profile)

    @personal_router.put("/profile")
    async def me_settings_profile_update(
        body: ProfileUpdatePayload,
        request: Request,
        response: Response,
        if_match: str | None = Header(default=None, alias="If-Match"),
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = container.profile_service
        try:
            current = await svc.get_profile(user_id)
        except ValueError as exc:
            _raise_profile_error(exc)
        assert_if_match(if_match, compute_etag(current))
        payload = body.model_dump(exclude_unset=True)
        subject = subject_from_claims(claims, user_id)
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
        return profile_payload(response, updated)

    @personal_router.post(
        "/profile/email/request-change",
        dependencies=[Depends(require_idempotency_key), Depends(csrf_protect)],
    )
    async def me_settings_email_request(
        payload: EmailChangePayload,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = container.profile_service
        subject = subject_from_claims(claims, user_id)
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

    @personal_router.post(
        "/profile/email/confirm",
        dependencies=[Depends(csrf_protect)],
    )
    async def me_settings_email_confirm(
        payload: EmailConfirmPayload,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = container.profile_service
        subject = subject_from_claims(claims, user_id)
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
        return profile_payload(response, updated)

    @personal_router.post(
        "/profile/wallet",
        dependencies=[Depends(csrf_protect)],
    )
    async def me_settings_wallet_bind(
        payload: WalletBindPayload,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = container.profile_service
        subject = subject_from_claims(claims, user_id)
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
        return profile_payload(response, updated)

    @personal_router.delete(
        "/profile/wallet",
        dependencies=[Depends(csrf_protect)],
    )
    async def me_settings_wallet_unbind(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        svc = container.profile_service
        subject = subject_from_claims(claims, user_id)
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
        return profile_payload(response, updated)


__all__ = [
    "EmailChangePayload",
    "EmailConfirmPayload",
    "ProfileUpdatePayload",
    "WalletBindPayload",
    "register",
]
