from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)
from domains.platform.notifications.application.messages_use_cases import (
    resolve_user_id,
)
from domains.platform.notifications.application.preferences_presenter import (
    build_ack_response,
    build_preferences_response,
)


@dataclass(slots=True)
class UseCaseResult:
    payload: dict[str, Any]
    status_code: int = 200


async def get_preferences(
    preference_service: Any,
    users_service: Any,
    *,
    subject: str | None,
    context: Mapping[str, Any] | None = None,
) -> UseCaseResult:
    user_id = await resolve_user_id(users_service, subject)
    preferences = await preference_service.get_preferences(
        user_id,
        context=context,
    )
    return UseCaseResult(payload=build_preferences_response(preferences))


async def set_preferences(
    preference_service: Any,
    users_service: Any,
    *,
    subject: str | None,
    preferences: Mapping[str, Any] | None,
) -> UseCaseResult:
    if preferences is None:
        raise NotificationError(code="invalid_preferences", status_code=400)
    if not isinstance(preferences, Mapping):
        raise NotificationError(
            code="invalid_preferences",
            status_code=400,
            message="preferences must be an object",
        )
    user_id = await resolve_user_id(users_service, subject)
    await preference_service.set_preferences(user_id, dict(preferences))
    return UseCaseResult(payload=build_ack_response())


__all__ = [
    "UseCaseResult",
    "get_preferences",
    "set_preferences",
]
