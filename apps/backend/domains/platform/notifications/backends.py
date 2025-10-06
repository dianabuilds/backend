from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.adapters.memory import (
    InMemoryBroadcastRepo,
    InMemoryNotificationConsentAuditRepo,
    InMemoryNotificationMatrixRepo,
    InMemoryNotificationPreferenceRepo,
    InMemoryNotificationRepository,
    InMemoryTemplateRepo,
)
from domains.platform.notifications.adapters.memory.audience import (
    InMemoryAudienceResolver,
)
from domains.platform.notifications.adapters.pusher_ws import WebSocketPusher
from domains.platform.notifications.adapters.sql.broadcasts import SQLBroadcastRepo
from domains.platform.notifications.adapters.sql.consent_audit import (
    SQLNotificationConsentAuditRepo,
)
from domains.platform.notifications.adapters.sql.matrix import SQLNotificationMatrixRepo
from domains.platform.notifications.adapters.sql.notifications import (
    NotificationRepository,
)
from domains.platform.notifications.adapters.sql.preferences import (
    SQLNotificationPreferenceRepo,
)
from domains.platform.notifications.adapters.sql.templates import SQLTemplateRepo
from domains.platform.notifications.adapters.ws_manager import WebSocketManager
from domains.platform.notifications.application.audience_resolver import (
    BroadcastAudienceResolver,
)
from domains.platform.notifications.application.broadcast_orchestrator import (
    BroadcastOrchestrator,
)
from domains.platform.notifications.application.broadcast_service import (
    BroadcastService,
)
from domains.platform.notifications.application.delivery import DeliveryService
from domains.platform.notifications.application.notify_service import NotifyService
from domains.platform.notifications.application.preference_service import (
    PreferenceService,
)
from domains.platform.notifications.application.template_service import (
    TemplateService,
)
from domains.platform.notifications.ports import (
    BroadcastRepo,
    NotificationConsentAuditRepo,
    NotificationMatrixRepo,
    NotificationPreferenceRepo,
    TemplateRepo,
)
from domains.platform.notifications.ports_notify import (
    INotificationRepository,
)
from packages.core.config import Settings, to_async_dsn


@dataclass(slots=True)
class NotificationsBackend:
    repo: INotificationRepository
    template_repo: TemplateRepo
    broadcast_repo: BroadcastRepo
    matrix_repo: NotificationMatrixRepo
    preference_repo: NotificationPreferenceRepo
    consent_audit_repo: NotificationConsentAuditRepo | None
    notify_service: NotifyService
    preference_service: PreferenceService
    broadcasts: BroadcastService
    templates: TemplateService
    ws_manager: WebSocketManager
    delivery: DeliveryService
    audience_resolver: Any
    orchestrator: BroadcastOrchestrator


def select_backend(
    settings: Settings,
    *,
    test_mode: bool,
    flag_service: FlagService | None,
) -> NotificationsBackend:
    ws_manager = WebSocketManager()
    pusher = WebSocketPusher(ws_manager)

    if test_mode or not getattr(settings, "database_url", None):
        template_repo: TemplateRepo = InMemoryTemplateRepo()
        broadcast_repo: BroadcastRepo = InMemoryBroadcastRepo()
        notification_repo: INotificationRepository = InMemoryNotificationRepository()
        matrix_repo: NotificationMatrixRepo = InMemoryNotificationMatrixRepo()
        preference_repo: NotificationPreferenceRepo = (
            InMemoryNotificationPreferenceRepo()
        )
        consent_repo: NotificationConsentAuditRepo | None = (
            InMemoryNotificationConsentAuditRepo()
        )
        audience_resolver = InMemoryAudienceResolver()
    else:
        async_dsn = to_async_dsn(settings.database_url)
        template_repo = SQLTemplateRepo(async_dsn)
        broadcast_repo = SQLBroadcastRepo(async_dsn)
        notification_repo = NotificationRepository(async_dsn)
        matrix_repo = SQLNotificationMatrixRepo(async_dsn)
        preference_repo = SQLNotificationPreferenceRepo(async_dsn)
        consent_repo = SQLNotificationConsentAuditRepo(async_dsn)
        audience_resolver = BroadcastAudienceResolver(async_dsn)

    template_service = TemplateService(template_repo)
    notify_service = NotifyService(notification_repo, pusher)
    preference_service = PreferenceService(
        matrix_repo=matrix_repo,
        preference_repo=preference_repo,
        audit_repo=consent_repo,
        flag_service=flag_service,
    )
    delivery_service = DeliveryService(
        matrix_repo=matrix_repo,
        preference_repo=preference_repo,
        notify_service=notify_service,
        template_service=template_service,
        flag_service=flag_service,
    )
    broadcasts = BroadcastService(broadcast_repo)
    orchestrator = BroadcastOrchestrator(
        repo=broadcast_repo,
        delivery=delivery_service,
        audience_resolver=audience_resolver,
        template_service=template_service,
    )

    return NotificationsBackend(
        repo=notification_repo,
        template_repo=template_repo,
        broadcast_repo=broadcast_repo,
        matrix_repo=matrix_repo,
        preference_repo=preference_repo,
        consent_audit_repo=consent_repo,
        notify_service=notify_service,
        preference_service=preference_service,
        broadcasts=broadcasts,
        templates=template_service,
        ws_manager=ws_manager,
        delivery=delivery_service,
        audience_resolver=audience_resolver,
        orchestrator=orchestrator,
    )


__all__ = ["NotificationsBackend", "select_backend"]
