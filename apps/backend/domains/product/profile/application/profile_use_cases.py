from __future__ import annotations

import io
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from domains.platform.media.application.storage_service import StorageService
from domains.product.profile.application.exceptions import (
    ProfileError,
    value_error_to_profile_error,
)
from domains.product.profile.application.profile_presenter import (
    build_avatar_response,
    build_email_change_response,
    build_profile_payload,
    build_profile_response,
    profile_etag,
)
from domains.product.profile.application.services import Service
from domains.product.profile.domain.results import EmailChangeRequest, ProfileView
from packages.core.errors import ApiError
from packages.core.settings_contract import assert_if_match

_NOT_FOUND_CODES = frozenset({"profile_not_found", "email_change_not_found"})


@dataclass(slots=True)
class UseCaseResult:
    payload: dict[str, Any]
    etag: str | None = None
    status_code: int = HTTPStatus.OK
    headers: Mapping[str, str] | None = None


def _profile_result(
    view: ProfileView, *, status: HTTPStatus = HTTPStatus.OK
) -> UseCaseResult:
    payload = build_profile_response(view)
    return UseCaseResult(payload=payload, etag=profile_etag(view), status_code=status)


def _wrap_api_error(error: ApiError) -> ProfileError:
    return ProfileError(
        code=error.code,
        status_code=error.status_code,
        message=error.message,
        headers=error.headers,
    )


def _normalize_subject(subject: Mapping[str, Any]) -> dict[str, Any]:
    return dict(subject)


async def get_profile_me(service: Service, user_id: str) -> UseCaseResult:
    try:
        view = await service.get_profile(user_id)
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc, fallback_status=HTTPStatus.NOT_FOUND, not_found_codes=_NOT_FOUND_CODES
        ) from exc
    return _profile_result(view)


async def get_profile_admin(service: Service, user_id: str) -> UseCaseResult:
    try:
        view = await service.get_profile(user_id)
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc, fallback_status=HTTPStatus.NOT_FOUND, not_found_codes=_NOT_FOUND_CODES
        ) from exc
    return _profile_result(view)


async def update_profile(
    service: Service,
    user_id: str,
    payload: Mapping[str, Any],
    *,
    subject: Mapping[str, Any],
    if_match: str | None,
    current: ProfileView | None = None,
) -> UseCaseResult:
    try:
        current_view = current or await service.get_profile(user_id)
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc, fallback_status=HTTPStatus.NOT_FOUND, not_found_codes=_NOT_FOUND_CODES
        ) from exc

    try:
        assert_if_match(if_match, profile_etag(current_view))
    except ApiError as api_error:
        raise _wrap_api_error(api_error) from api_error

    try:
        updated = await service.update_profile(
            user_id,
            dict(payload),
            subject=_normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=_NOT_FOUND_CODES,
        ) from exc

    return _profile_result(updated)


async def legacy_update_username(
    service: Service,
    user_id: str,
    username: str,
    *,
    subject: Mapping[str, Any],
) -> UseCaseResult:
    if not isinstance(username, str) or not username.strip():
        raise ProfileError(code="username_required", status_code=HTTPStatus.BAD_REQUEST)

    trimmed_username = username.strip()

    try:
        updated = await service.update_profile(
            user_id,
            {"username": trimmed_username},
            subject=_normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=_NOT_FOUND_CODES,
        ) from exc

    return _profile_result(updated)


async def request_email_change(
    service: Service,
    user_id: str,
    email: str,
    *,
    subject: Mapping[str, Any],
) -> UseCaseResult:
    try:
        result: EmailChangeRequest = await service.request_email_change(
            user_id,
            email,
            subject=_normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=_NOT_FOUND_CODES,
        ) from exc

    payload = build_email_change_response(result)
    return UseCaseResult(payload=payload)


async def confirm_email_change(
    service: Service,
    user_id: str,
    token: str,
    *,
    subject: Mapping[str, Any],
) -> UseCaseResult:
    try:
        updated = await service.confirm_email_change(
            user_id,
            token,
            subject=_normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=_NOT_FOUND_CODES,
        ) from exc

    return _profile_result(updated)


async def bind_wallet(
    service: Service,
    user_id: str,
    payload: Mapping[str, Any],
    *,
    subject: Mapping[str, Any],
) -> UseCaseResult:
    address_raw = payload.get("address")
    chain_id_raw = payload.get("chain_id")
    signature = payload.get("signature")

    if not isinstance(address_raw, str):
        raise ProfileError(code="wallet_required", status_code=HTTPStatus.BAD_REQUEST)

    address = address_raw.strip()
    if not address:
        raise ProfileError(code="wallet_required", status_code=HTTPStatus.BAD_REQUEST)

    chain_id = chain_id_raw.strip() if isinstance(chain_id_raw, str) else None

    try:
        updated = await service.set_wallet(
            user_id,
            address=address,
            chain_id=chain_id,
            signature=signature if isinstance(signature, str) else None,
            subject=_normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=_NOT_FOUND_CODES,
        ) from exc

    return _profile_result(updated)


async def unbind_wallet(
    service: Service,
    user_id: str,
    *,
    subject: Mapping[str, Any],
) -> UseCaseResult:
    try:
        updated = await service.clear_wallet(user_id, _normalize_subject(subject))
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=_NOT_FOUND_CODES,
        ) from exc

    return _profile_result(updated)


async def upload_avatar(
    storage: StorageService,
    *,
    file_name: str,
    content: bytes,
    content_type: str,
    max_size: int,
    allowed_types: set[str],
) -> UseCaseResult:
    if content_type not in allowed_types:
        raise ProfileError(
            code="unsupported_media_type", status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE
        )

    if len(content) > max_size:
        raise ProfileError(
            code="file_too_large", status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE
        )

    name = file_name or "avatar"
    url = storage.save_file(io.BytesIO(content), name, content_type)
    return UseCaseResult(payload=build_avatar_response(url))


async def build_profile_settings_payload(view: ProfileView) -> UseCaseResult:
    payload = build_profile_payload(view)
    return UseCaseResult(payload=payload, etag=profile_etag(view))


__all__ = [
    "UseCaseResult",
    "bind_wallet",
    "build_profile_settings_payload",
    "confirm_email_change",
    "get_profile_admin",
    "get_profile_me",
    "legacy_update_username",
    "request_email_change",
    "unbind_wallet",
    "update_profile",
    "upload_avatar",
]
