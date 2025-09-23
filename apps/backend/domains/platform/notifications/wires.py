from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.events.service import Events
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
    SQLCampaignRepo,
    SQLTemplateRepo,
)
from domains.platform.notifications.adapters.ws_manager import (
    WebSocketManager,
)
from domains.platform.notifications.application.campaign_service import (
    CampaignService,
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
from packages.core.config import Settings, load_settings, to_async_dsn


def register_event_relays(events: Events, topics: list[str]) -> None:
    def _handler(_topic: str, payload: dict[str, Any]) -> None:
        try:
            dispatch("log", payload)
        except Exception:
            # Swallow to avoid breaking bus in demo wiring
            pass

    for t in topics:
        events.on(t, _handler)


@dataclass
class NotificationsContainer:
    settings: Settings
    notify_service: NotifyService
    preference_service: PreferenceService
    campaigns: CampaignService
    templates: TemplateService
    repo: NotificationRepository
    notify: NotifyService
    ws_manager: WebSocketManager


def build_container(settings: Settings | None = None) -> NotificationsContainer:
    s = settings or load_settings()
    repo = SQLCampaignRepo(to_async_dsn(s.database_url))
    campaigns = CampaignService(repo)
    templates_repo = SQLTemplateRepo(to_async_dsn(s.database_url))
    templates = TemplateService(templates_repo)
    notif_repo = NotificationRepository(to_async_dsn(s.database_url))
    ws_manager = WebSocketManager()
    pusher = WebSocketPusher(ws_manager)
    notify_service = NotifyService(notif_repo, pusher)
    pref_repo = SQLNotificationPreferenceRepo(to_async_dsn(s.database_url))
    preference_service = PreferenceService(pref_repo)
    return NotificationsContainer(
        settings=s,
        notify_service=notify_service,
        preference_service=preference_service,
        campaigns=campaigns,
        templates=templates,
        repo=notif_repo,
        notify=notify_service,
        ws_manager=ws_manager,
    )


__all__ = ["register_event_relays", "NotificationsContainer", "build_container"]
