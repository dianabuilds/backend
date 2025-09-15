from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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


__all__ = ["Notification"]
