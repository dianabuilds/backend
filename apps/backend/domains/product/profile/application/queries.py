from __future__ import annotations

from http import HTTPStatus

from domains.product.profile.application.exceptions import (
    value_error_to_profile_error,
)
from domains.product.profile.application.services import Service
from domains.product.profile.domain.results import ProfileView

from .constants import NOT_FOUND_CODES
from .profile_presenter import (
    ProfileEnvelope,
    ProfilePayload,
    ResponseMeta,
    build_profile_result,
    build_profile_settings_result,
)


async def get_profile_me(
    service: Service, user_id: str
) -> tuple[ProfilePayload, ResponseMeta]:
    try:
        view = await service.get_profile(user_id)
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.NOT_FOUND,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc
    return build_profile_result(view)


async def get_profile_admin(
    service: Service, user_id: str
) -> tuple[ProfilePayload, ResponseMeta]:
    try:
        view = await service.get_profile(user_id)
    except ValueError as exc:
        raise value_error_to_profile_error(
            exc,
            fallback_status=HTTPStatus.NOT_FOUND,
            not_found_codes=NOT_FOUND_CODES,
        ) from exc
    return build_profile_result(view)


async def build_profile_settings_payload(
    view: ProfileView,
) -> tuple[ProfileEnvelope, ResponseMeta]:
    return build_profile_settings_result(view)


__all__ = [
    "build_profile_settings_payload",
    "get_profile_admin",
    "get_profile_me",
]
