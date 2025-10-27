from __future__ import annotations

import asyncio
import logging
from asyncio import TimeoutError as AsyncTimeoutError
from collections.abc import Coroutine
from concurrent.futures import Future as ThreadFuture
from dataclasses import dataclass
from typing import Any

from domains.platform.events.application.publisher import Events
from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.application.delivery import (
    DeliveryService,
    NotificationEvent,
)
from domains.platform.notifications.backends import select_backend
from domains.platform.notifications.logic.dispatcher import dispatch
from domains.platform.notifications.ports import (
    NotificationConsentAuditRepo,
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
)
from domains.platform.notifications.ports_notify import INotificationRepository
from packages.core.async_utils import run_sync
from packages.core.config import Settings, load_settings
from packages.core.testing import is_test_mode

logger = logging.getLogger(__name__)
_DELIVERY_ERRORS = (
    RuntimeError,
    ValueError,
    ConnectionError,
    AsyncTimeoutError,
    OSError,
)


def _dispatch_with_log(action: str, payload: dict[str, Any]) -> None:
    try:
        dispatch(action, payload)
    except _DELIVERY_ERRORS as exc:
        logger.debug("Notifications dispatcher '%s' failed", action, exc_info=exc)


def register_event_relays(
    events: Events,
    topics: list[str],
    delivery: DeliveryService | None = None,
    *,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    try:
        target_loop = loop or asyncio.get_running_loop()
    except RuntimeError:
        target_loop = None

    def _log_future_result(fut: ThreadFuture[None]) -> None:
        exc = fut.exception()
        if exc:
            logger.exception("Notifications delivery task failed", exc_info=exc)

    def _log_task_result(task: asyncio.Future[Any]) -> None:
        exc = task.exception()
        if exc:
            logger.exception("Notifications delivery task failed", exc_info=exc)

    def _submit_delivery(coro: Coroutine[Any, Any, None]) -> None:
        nonlocal target_loop
        if target_loop and not target_loop.is_closed():
            future: ThreadFuture[None] = asyncio.run_coroutine_threadsafe(
                coro, target_loop
            )
            future.add_done_callback(_log_future_result)
        else:
            try:
                run_sync(coro)
            except _DELIVERY_ERRORS as exc:
                logger.exception("Notifications delivery task failed", exc_info=exc)

    def _handler(topic: str, payload: dict[str, Any]) -> None:
        if delivery is None:
            _dispatch_with_log("log", payload)
            return
        try:
            event = NotificationEvent.from_payload(topic, payload)
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Failed to convert notification payload for topic %s: %s", topic, exc
            )
            _dispatch_with_log("log", payload)
            return

        async def _deliver() -> None:
            try:
                await delivery.deliver_to_inbox(event)
            except _DELIVERY_ERRORS as exc:
                logger.exception(
                    "Notifications delivery failed for topic=%s user=%s",
                    event.topic,
                    event.user_id,
                    exc_info=exc,
                )

        try:
            loop_running = asyncio.get_running_loop()
        except RuntimeError:
            _submit_delivery(_deliver())
        else:
            task = loop_running.create_task(_deliver())
            task.add_done_callback(_log_task_result)
        _dispatch_with_log("log", payload)

    for t in topics:
        events.on(t, _handler)


@dataclass
class NotificationsContainer:
    settings: Settings
    notify_service: Any
    preference_service: Any
    broadcasts: Any
    templates: Any
    repo: INotificationRepository
    notify: Any
    ws_manager: Any
    matrix_repo: NotificationMatrixRepo
    preference_repo: NotificationPreferenceRepo
    config_repo: Any
    consent_audit_repo: NotificationConsentAuditRepo | None
    flag_service: FlagService | None
    audience_resolver: Any
    orchestrator: Any
    delivery: DeliveryService
    retention_service: Any


def build_container(
    settings: Settings | None = None,
    *,
    flag_service: FlagService | None = None,
) -> NotificationsContainer:
    s = settings or load_settings()
    backend = select_backend(s, test_mode=is_test_mode(s), flag_service=flag_service)
    return NotificationsContainer(
        settings=s,
        notify_service=backend.notify_service,
        preference_service=backend.preference_service,
        broadcasts=backend.broadcasts,
        templates=backend.templates,
        repo=backend.repo,
        notify=backend.notify_service,
        ws_manager=backend.ws_manager,
        matrix_repo=backend.matrix_repo,
        preference_repo=backend.preference_repo,
        config_repo=backend.config_repo,
        consent_audit_repo=backend.consent_audit_repo,
        flag_service=flag_service,
        audience_resolver=backend.audience_resolver,
        orchestrator=backend.orchestrator,
        delivery=backend.delivery,
        retention_service=backend.retention_service,
    )


__all__ = ["register_event_relays", "NotificationsContainer", "build_container"]
