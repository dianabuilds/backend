from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Notification:
    id: str
    user_id: str
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None
    type: str
    placement: str
    is_preview: bool
    topic_key: str | None = None
    channel_key: str | None = None
    priority: str = "normal"
    cta_label: str | None = None
    cta_url: str | None = None
    event_id: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime | None = None


__all__ = ["Notification"]
