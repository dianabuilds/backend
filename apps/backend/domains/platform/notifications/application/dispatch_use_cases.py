from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)


@dataclass(slots=True)
class UseCaseResult:
    payload: dict[str, Any]
    status_code: int = 200


def preview_channel_notification(
    dispatcher: Callable[[str, dict[str, Any]], None],
    *,
    channel: str,
    payload: dict[str, Any] | None,
    logger: logging.Logger | None = None,
) -> UseCaseResult:
    data = payload or {}
    try:
        dispatcher(channel, data)
    except RuntimeError as exc:
        if logger:
            logger.warning(
                "notification_dispatch_failed",
                extra={"channel": channel},
                exc_info=exc,
            )
        raise NotificationError(code="publish_failed", status_code=502) from exc
    return UseCaseResult(payload={"ok": True})


def send_channel_notification(
    dispatcher: Callable[[str, dict[str, Any]], None],
    validator: Callable[[str, str, dict[str, Any]], None],
    *,
    channel: str,
    payload: dict[str, Any],
    logger: logging.Logger | None = None,
    validation_errors: Sequence[type[Exception]] = (),
) -> UseCaseResult:
    request_body = {"channel": channel, "payload": payload}
    try:
        validator("/v1/notifications/send", "post", request_body)
    except Exception as exc:  # noqa: BLE001 - controlled translation
        if validation_errors and not isinstance(exc, tuple(validation_errors)):
            raise
        if logger:
            logger.info(
                "notification_payload_invalid",
                extra={"channel": channel},
                exc_info=exc,
            )
        raise NotificationError(
            code="schema_validation_failed", status_code=422
        ) from exc
    try:
        dispatcher(channel, payload)
    except RuntimeError as exc:
        if logger:
            logger.warning(
                "notification_dispatch_failed",
                extra={"channel": channel},
                exc_info=exc,
            )
        raise NotificationError(code="publish_failed", status_code=502) from exc
    return UseCaseResult(payload={"ok": True})


__all__ = [
    "UseCaseResult",
    "send_channel_notification",
    "preview_channel_notification",
]
