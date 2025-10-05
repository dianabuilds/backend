from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Request, Response, status
from pydantic import BaseModel, Field

from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from domains.product.profile.application.exceptions import ProfileError
from domains.product.profile.application.profile_use_cases import (
    bind_wallet,
    confirm_email_change,
    get_profile_admin,
    get_profile_me,
    request_email_change,
    unbind_wallet,
    update_profile,
)
from packages.core.errors import ApiError
from packages.core.settings_contract import attach_settings_schema

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
    "forbidden": (
        status.HTTP_403_FORBIDDEN,
        "E_FORBIDDEN",
        "Operation forbidden",
    ),
}


def _raise_profile_error(error: ProfileError) -> None:
    status_code, code, message = _PROFILE_ERROR_MAP.get(
        error.code,
        (
            error.status_code,
            error.code if error.code.startswith("E_") else "E_PROFILE_INVALID",
            error.message or error.code,
        ),
    )
    headers = dict(error.headers) if error.headers else None
    raise ApiError(
        code=code, status_code=status_code, message=message, headers=headers
    ) from error


def _profile_response(
    response: Response, result_payload: dict[str, Any], status_code: int | None = None
) -> dict[str, Any]:
    if status_code is not None:
        response.status_code = status_code
    return profile_payload(response, result_payload)


def _apply_result_headers(response: Response, headers: dict[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        response.headers[key] = value


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
        try:
            result = await get_profile_admin(container.profile_service, user_id)
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))

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
        subject = subject_from_claims(claims, user_id)
        subject.setdefault("role", "admin")
        try:
            result = await update_profile(
                container.profile_service,
                user_id,
                body.model_dump(exclude_unset=True),
                subject=subject,
                if_match=if_match,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))

    @personal_router.get("/profile")
    async def me_settings_profile_get(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = require_user_id(claims)
        container = get_container(request)
        try:
            result = await get_profile_me(container.profile_service, user_id)
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))

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
        subject = subject_from_claims(claims, user_id)
        try:
            result = await update_profile(
                container.profile_service,
                user_id,
                body.model_dump(exclude_unset=True),
                subject=subject,
                if_match=if_match,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))

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
        subject = subject_from_claims(claims, user_id)
        try:
            result = await request_email_change(
                container.profile_service,
                user_id,
                payload.email,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return attach_settings_schema(result.payload, response)

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
        subject = subject_from_claims(claims, user_id)
        try:
            result = await confirm_email_change(
                container.profile_service,
                user_id,
                payload.token,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))

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
        subject = subject_from_claims(claims, user_id)
        try:
            result = await bind_wallet(
                container.profile_service,
                user_id,
                payload.model_dump(exclude_unset=True),
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))

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
        subject = subject_from_claims(claims, user_id)
        try:
            result = await unbind_wallet(
                container.profile_service,
                user_id,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        _apply_result_headers(
            response, dict(result.headers) if result.headers else None
        )
        return _profile_response(response, result.payload, int(result.status_code))


__all__ = [
    "EmailChangePayload",
    "EmailConfirmPayload",
    "ProfileUpdatePayload",
    "WalletBindPayload",
    "register",
]
