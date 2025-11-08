from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.pool import NullPool

from domains.platform.flags.application.service import FlagService
from domains.platform.notifications.adapters.memory import (
    InMemoryBroadcastRepo,
    InMemoryNotificationConfigRepository,
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
from domains.platform.notifications.adapters.sql.config import (
    NotificationConfigRepository as SQLNotificationConfigRepository,
)
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
from domains.platform.notifications.application.retention_service import (
    NotificationRetentionService,
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
from packages.core.async_utils import run_sync
from packages.core.config import Settings
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

logger = logging.getLogger(__name__)


async def _ping_notifications_engine(engine) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


def _probe_notifications_sql_backend(dsn: str) -> tuple[bool, str | None]:
    engine = get_async_engine(
        "notifications.probe",
        url=dsn,
        cache=False,
        pool_pre_ping=False,
        poolclass=NullPool,
        connect_args={"timeout": 2},
    )
    try:
        run_sync(_ping_notifications_engine(engine))
        return True, None
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Notifications SQL backend probe failed", exc_info=exc)
        return False, str(exc)
    finally:
        try:
            run_sync(engine.dispose())
        except Exception:  # pragma: no cover - best-effort cleanup
            logger.debug("Notifications probe dispose failed", exc_info=True)


def _resolve_notifications_dsn(
    settings: Settings,
    *,
    test_mode: bool,
) -> tuple[str | None, str | None]:
    if test_mode:
        return None, "test mode disallows SQL backend"
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        return None, decision.reason
    ok, probe_reason = _probe_notifications_sql_backend(decision.dsn)
    if not ok:
        return None, probe_reason or "database probe failed"
    return decision.dsn, None


@dataclass(slots=True)
class NotificationsBackend:
    repo: INotificationRepository
    template_repo: TemplateRepo
    broadcast_repo: BroadcastRepo
    matrix_repo: NotificationMatrixRepo
    preference_repo: NotificationPreferenceRepo
    config_repo: Any
    consent_audit_repo: NotificationConsentAuditRepo | None
    notify_service: NotifyService
    preference_service: PreferenceService
    broadcasts: BroadcastService
    templates: TemplateService
    ws_manager: WebSocketManager
    delivery: DeliveryService
    audience_resolver: Any
    orchestrator: BroadcastOrchestrator
    retention_service: NotificationRetentionService


def select_backend(
    settings: Settings,
    *,
    test_mode: bool,
    flag_service: FlagService | None,
) -> NotificationsBackend:
    ws_manager = WebSocketManager()
    pusher = WebSocketPusher(ws_manager)

    async_dsn, fallback_reason = _resolve_notifications_dsn(
        settings, test_mode=test_mode
    )
    if not async_dsn:
        if fallback_reason:
            logger.info(
                "Notifications backend: using in-memory repositories (%s)",
                fallback_reason,
            )
        else:
            logger.info(
                "Notifications backend: using in-memory repositories (SQL disabled)"
            )
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
        config_repo = InMemoryNotificationConfigRepository()
    else:
        template_repo = SQLTemplateRepo(async_dsn)
        broadcast_repo = SQLBroadcastRepo(async_dsn)
        notification_repo = NotificationRepository(async_dsn)
        matrix_repo = SQLNotificationMatrixRepo(async_dsn)
        preference_repo = SQLNotificationPreferenceRepo(async_dsn)
        consent_repo = SQLNotificationConsentAuditRepo(async_dsn)
        audience_resolver = BroadcastAudienceResolver(async_dsn)
        config_repo = SQLNotificationConfigRepository(async_dsn)

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
        retention_days=getattr(settings.notifications, "retention_days", None),
        max_per_user=getattr(settings.notifications, "max_per_user", None),
    )
    retention_service = NotificationRetentionService(
        config_repo,
        settings,
        delivery_service,
    )
    try:
        run_sync(retention_service.refresh_delivery())
    except Exception:
        pass
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
        config_repo=config_repo,
        consent_audit_repo=consent_repo,
        notify_service=notify_service,
        preference_service=preference_service,
        broadcasts=broadcasts,
        templates=template_service,
        ws_manager=ws_manager,
        delivery=delivery_service,
        audience_resolver=audience_resolver,
        orchestrator=orchestrator,
        retention_service=retention_service,
    )


__all__ = ["NotificationsBackend", "select_backend"]
