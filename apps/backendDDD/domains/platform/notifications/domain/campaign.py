from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Campaign:
    id: str
    title: str
    message: str
    type: str
    filters: dict[str, Any] | None
    status: str
    total: int
    sent: int
    failed: int
    created_by: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


__all__ = ["Campaign"]
