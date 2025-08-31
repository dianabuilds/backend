from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AuditEntry:
    actor_id: UUID | None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    before: Any = None
    after: Any = None
    ip: str | None = None
    user_agent: str | None = None
    extra: Any = None

    def __post_init__(self) -> None:
        if not self.action or not self.action.strip():
            raise ValueError("action must be a non-empty string")
