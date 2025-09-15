from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.events.service import Events
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


from domains.platform.notifications.adapters.notification_repository_sql import (
    NotificationRepository,
)
from domains.platform.notifications.adapters.pusher_ws import (
    WebSocketPusher,
)
from domains.platform.notifications.adapters.repos_sql import (
    SQLCampaignRepo,
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


@dataclass
class NotificationsContainer:
    campaigns: CampaignService
    repo: NotificationRepository
    notify: NotifyService
    ws_manager: WebSocketManager


def build_container(settings: Settings | None = None) -> NotificationsContainer:
    s = settings or load_settings()
    repo = SQLCampaignRepo(to_async_dsn(s.database_url))
    svc = CampaignService(repo)
    nrepo = NotificationRepository(to_async_dsn(s.database_url))
    ws_manager = WebSocketManager()
    pusher = WebSocketPusher(ws_manager)
    notify = NotifyService(nrepo, pusher)
    return NotificationsContainer(
        campaigns=svc, repo=nrepo, notify=notify, ws_manager=ws_manager
    )


__all__ = ["register_event_relays", "NotificationsContainer", "build_container"]
