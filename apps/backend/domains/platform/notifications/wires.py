from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from concurrent.futures import Future as ThreadFuture
from dataclasses import dataclass
from typing import Any

from domains.platform.events.service import Events
from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.adapters.broadcast_sql import SQLBroadcastRepo
from domains.platform.notifications.adapters.consent_audit_sql import (
    SQLNotificationConsentAuditRepo,
)
from domains.platform.notifications.adapters.matrix_sql import (
    SQLNotificationMatrixRepo,
)
from domains.platform.notifications.adapters.notification_repository_sql import (
    NotificationRepository,
)
from domains.platform.notifications.adapters.pusher_ws import (
    WebSocketPusher,
)
from domains.platform.notifications.adapters.repo_sql import (
    SQLNotificationPreferenceRepo,
)
from domains.platform.notifications.adapters.repos_sql import (
    SQLTemplateRepo,
)
from domains.platform.notifications.adapters.ws_manager import (
    WebSocketManager,
)
from domains.platform.notifications.application.audience_resolver import (
    BroadcastAudienceResolver,
)
from domains.platform.notifications.application.broadcast_orchestrator import (
    BroadcastOrchestrator,
)
from domains.platform.notifications.application.broadcast_service import (
    BroadcastService,
)
from domains.platform.notifications.application.delivery_service import (
    DeliveryService,
    NotificationEvent,
)
from domains.platform.notifications.application.notify_service import (
    NotifyService,
)
from domains.platform.notifications.application.preference_service import (
    PreferenceService,
)
from domains.platform.notifications.application.template_service import (
    TemplateService,
)
from domains.platform.notifications.logic.dispatcher import dispatch
from packages.core.async_utils import run_sync
from packages.core.config import Settings, load_settings, to_async_dsn

logger = logging.getLogger(__name__)


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
        try:
            fut.result()
        except Exception as exc:
            logger.exception("Notifications delivery task failed", exc_info=exc)

    def _log_task_result(task: asyncio.Future[Any]) -> None:
        try:
            task.result()
        except Exception as exc:
            logger.exception("Notifications delivery task failed", exc_info=exc)

    def _submit_delivery(coro: Awaitable[None]) -> None:
        nonlocal target_loop
        if target_loop and not target_loop.is_closed():
            future = asyncio.run_coroutine_threadsafe(coro, target_loop)
            future.add_done_callback(_log_future_result)
        else:
            try:
                run_sync(coro)
            except Exception as exc:
                logger.exception("Notifications delivery task failed", exc_info=exc)

    def _handler(topic: str, payload: dict[str, Any]) -> None:
        if delivery is not None:
            try:
                event = NotificationEvent.from_payload(topic, payload)
            except Exception:
                try:
                    dispatch("log", payload)
                except Exception:
                    pass
                return

            async def _deliver() -> None:
                try:
                    await delivery.deliver_to_inbox(event)
                except Exception as exc:
                    logger.exception("Notifications delivery failed", exc_info=exc)

            try:
                loop_running = asyncio.get_running_loop()
            except RuntimeError:
                _submit_delivery(_deliver())
            else:
                task = loop_running.create_task(_deliver())
                task.add_done_callback(_log_task_result)
            try:
                dispatch("log", payload)
            except Exception:
                pass
            return
        try:
            dispatch("log", payload)
        except Exception:
            pass

    for t in topics:
        events.on(t, _handler)


@dataclass
class NotificationsContainer:
    settings: Settings
    notify_service: NotifyService
    preference_service: PreferenceService
    broadcasts: BroadcastService
    templates: TemplateService
    repo: NotificationRepository
    notify: NotifyService
    ws_manager: WebSocketManager
    matrix_repo: SQLNotificationMatrixRepo
    preference_repo: SQLNotificationPreferenceRepo
    consent_audit_repo: SQLNotificationConsentAuditRepo | None
    flag_service: FlagService | None
    audience_resolver: BroadcastAudienceResolver
    orchestrator: BroadcastOrchestrator
    delivery: DeliveryService


def build_container(
    settings: Settings | None = None,
    *,
    flag_service: FlagService | None = None,
) -> NotificationsContainer:
    s = settings or load_settings()
    async_dsn = to_async_dsn(s.database_url)
    broadcast_repo = SQLBroadcastRepo(async_dsn)
    broadcasts = BroadcastService(broadcast_repo)
    templates_repo = SQLTemplateRepo(async_dsn)
    templates = TemplateService(templates_repo)
    notif_repo = NotificationRepository(async_dsn)
    ws_manager = WebSocketManager()
    pusher = WebSocketPusher(ws_manager)
    notify_service = NotifyService(notif_repo, pusher)
    pref_repo = SQLNotificationPreferenceRepo(async_dsn)
    matrix_repo = SQLNotificationMatrixRepo(async_dsn)
    audit_repo = SQLNotificationConsentAuditRepo(async_dsn)
    preference_service = PreferenceService(
        matrix_repo=matrix_repo,
        preference_repo=pref_repo,
        audit_repo=audit_repo,
        flag_service=flag_service,
    )
    delivery_service = DeliveryService(
        matrix_repo=matrix_repo,
        preference_repo=pref_repo,
        notify_service=notify_service,
        template_service=templates,
        flag_service=flag_service,
    )

    audience_resolver = BroadcastAudienceResolver(async_dsn)
    orchestrator = BroadcastOrchestrator(
        repo=broadcast_repo,
        delivery=delivery_service,
        audience_resolver=audience_resolver,
        template_service=templates,
    )

    return NotificationsContainer(
        settings=s,
        notify_service=notify_service,
        preference_service=preference_service,
        broadcasts=broadcasts,
        templates=templates,
        repo=notif_repo,
        notify=notify_service,
        ws_manager=ws_manager,
        matrix_repo=matrix_repo,
        preference_repo=pref_repo,
        consent_audit_repo=audit_repo,
        flag_service=flag_service,
        audience_resolver=audience_resolver,
        orchestrator=orchestrator,
        delivery=delivery_service,
    )


__all__ = ["register_event_relays", "NotificationsContainer", "build_container"]
