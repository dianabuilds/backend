from __future__ import annotations

import io
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from domains.platform.media.application.facade import StorageService
from domains.product.profile.application.exceptions import (
    ProfileError,
    value_error_to_profile_error,
)
from domains.product.profile.application.services import Service
from domains.product.profile.domain.results import EmailChangeRequest, ProfileView
from packages.core.errors import ApiError
from packages.core.settings_contract import assert_if_match

from .constants import NOT_FOUND_CODES, normalize_subject
from .profile_presenter import (
    AvatarResponse,
    EmailChangeResponse,
    ProfilePayload,
    ResponseMeta,
    build_avatar_result,
    build_email_change_result,
    build_profile_result,
    profile_etag,
)


def _wrap_api_error(error: ApiError) -> ProfileError:
    return ProfileError(
        code=error.code,
        status_code=error.status_code,
        message=error.message,
        headers=error.headers,
    )


async def update_profile(
    service: Service,
    user_id: str,
    payload: Mapping[str, Any],
    *,
    subject: Mapping[str, Any],
    if_match: str | None,
    current: ProfileView | None = None,
) -> tuple[ProfilePayload, ResponseMeta]:
    try:
        current_view = current or await service.get_profile(user_id)
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.NOT_FOUND,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    try:
        assert_if_match(if_match, profile_etag(current_view))
    except ApiError as api_error:
        raise _wrap_api_error(api_error) from api_error

    try:
        updated = await service.update_profile(
            user_id,
            dict(payload),
            subject=normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    return build_profile_result(updated)


async def legacy_update_username(
    service: Service,
    user_id: str,
    username: str,
    *,
    subject: Mapping[str, Any],
) -> tuple[ProfilePayload, ResponseMeta]:
    if not isinstance(username, str) or not username.strip():
        raise ProfileError(code="username_required", status_code=HTTPStatus.BAD_REQUEST)

    trimmed_username = username.strip()

    try:
        updated = await service.update_profile(
            user_id,
            {"username": trimmed_username},
            subject=normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    return build_profile_result(updated)


async def request_email_change(
    service: Service,
    user_id: str,
    email: str,
    *,
    subject: Mapping[str, Any],
) -> tuple[EmailChangeResponse, ResponseMeta]:
    try:
        result: EmailChangeRequest = await service.request_email_change(
            user_id,
            email,
            subject=normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    return build_email_change_result(result)


async def confirm_email_change(
    service: Service,
    user_id: str,
    token: str,
    *,
    subject: Mapping[str, Any],
) -> tuple[ProfilePayload, ResponseMeta]:
    try:
        updated = await service.confirm_email_change(
            user_id,
            token,
            subject=normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    return build_profile_result(updated)


async def bind_wallet(
    service: Service,
    user_id: str,
    payload: Mapping[str, Any],
    *,
    subject: Mapping[str, Any],
) -> tuple[ProfilePayload, ResponseMeta]:
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
            subject=normalize_subject(subject),
        )
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    return build_profile_result(updated)


async def unbind_wallet(
    service: Service,
    user_id: str,
    *,
    subject: Mapping[str, Any],
) -> tuple[ProfilePayload, ResponseMeta]:
    try:
        updated = await service.clear_wallet(user_id, normalize_subject(subject))
    except PermissionError as exc:
        raise ProfileError(code="forbidden", status_code=HTTPStatus.FORBIDDEN) from exc
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.BAD_REQUEST,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc

    return build_profile_result(updated)


async def upload_avatar(
    storage: StorageService,
    *,
    file_name: str,
    content: bytes,
    content_type: str,
    max_size: int,
    allowed_types: set[str],
) -> tuple[AvatarResponse, ResponseMeta]:
    if content_type not in allowed_types:
        raise ProfileError(
            code="unsupported_media_type",
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    if len(content) > max_size:
        raise ProfileError(
            code="file_too_large",
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )

    name = file_name or "avatar"
    url = storage.save_file(io.BytesIO(content), name, content_type)
    return build_avatar_result(url)


__all__ = [
    "bind_wallet",
    "confirm_email_change",
    "legacy_update_username",
    "request_email_change",
    "unbind_wallet",
    "update_profile",
    "upload_avatar",
]
