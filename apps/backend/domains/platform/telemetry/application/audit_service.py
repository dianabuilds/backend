from __future__ import annotations

from typing import Any
from uuid import UUID

from domains.platform.telemetry.domain.audit import AuditEntry
from domains.platform.telemetry.ports.audit_port import (
    IAuditLogRepository,
)


class AuditService:
    def __init__(self, repo: IAuditLogRepository) -> None:
        self._repo = repo

    async def log(
        self,
        *,
        actor_id: str | UUID | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        before: Any = None,
        after: Any = None,
        ip: str | None = None,
        user_agent: str | None = None,
        reason: str | None = None,
        extra: Any = None,
    ) -> None:
        normalized_actor_id: UUID | None = None
        if isinstance(actor_id, UUID):
            normalized_actor_id = actor_id
        elif isinstance(actor_id, str) and actor_id:
            try:
                normalized_actor_id = UUID(actor_id)
            except Exception:
                normalized_actor_id = None

        extras = {"reason": reason} if reason else (extra or None)

        entry = AuditEntry(
            actor_id=normalized_actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before=before,
            after=after,
            ip=ip,
            user_agent=user_agent,
            extra=extras,
        )
        await self._repo.add(entry)


__all__ = ["AuditService"]
