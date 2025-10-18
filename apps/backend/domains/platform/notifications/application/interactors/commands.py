from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NotificationCreateCommand:
    user_id: str
    title: str
    message: str
    type_: str
    placement: str = "inbox"
    is_preview: bool = False
    topic_key: str | None = None
    channel_key: str | None = None
    priority: str = "normal"
    cta_label: str | None = None
    cta_url: str | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)
    event_id: str | None = None

    def to_repo_payload(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type_": self.type_,
            "placement": self.placement,
            "is_preview": self.is_preview,
            "topic_key": self.topic_key,
            "channel_key": self.channel_key,
            "priority": self.priority,
            "cta_label": self.cta_label,
            "cta_url": self.cta_url,
            "meta": dict(self.meta),
            "event_id": self.event_id,
        }


__all__ = ["NotificationCreateCommand"]
