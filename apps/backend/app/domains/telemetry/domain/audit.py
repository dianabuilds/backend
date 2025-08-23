from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID


@dataclass(frozen=True)
class AuditEntry:
    actor_id: Optional[UUID]
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    before: Any = None
    after: Any = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    extra: Any = None

    def __post_init__(self) -> None:
        if not self.action or not self.action.strip():
            raise ValueError("action must be a non-empty string")
