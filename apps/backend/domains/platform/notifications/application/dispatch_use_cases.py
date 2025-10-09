from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any, TypedDict

from domains.platform.notifications.application.messages_exceptions import (
    NotificationError,
)


class DispatchAck(TypedDict):
    ok: bool


def preview_channel_notification(
    dispatcher: Callable[[str, dict[str, Any]], None],
    *,
    channel: str,
    payload: dict[str, Any] | None,
    logger: logging.Logger | None = None,
) -> DispatchAck:
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
    return DispatchAck(ok=True)


def send_channel_notification(
    dispatcher: Callable[[str, dict[str, Any]], None],
    validator: Callable[[str, str, dict[str, Any]], None],
    *,
    channel: str,
    payload: dict[str, Any],
    logger: logging.Logger | None = None,
    validation_errors: Sequence[type[Exception]] = (),
) -> DispatchAck:
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
    return DispatchAck(ok=True)


__all__ = [
    "DispatchAck",
    "send_channel_notification",
    "preview_channel_notification",
]
