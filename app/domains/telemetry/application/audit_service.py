from __future__ import annotations

from typing import Any, Optional, Union
from uuid import UUID

from app.domains.telemetry.domain.audit import AuditEntry
from app.domains.telemetry.application.ports.audit_port import IAuditLogRepository


class AuditService:
    def __init__(self, repo: IAuditLogRepository) -> None:
        self._repo = repo

    async def log(
        self,
        *,
        actor_id: Optional[Union[str, UUID]],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        before: Any = None,
        after: Any = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
        extra: Any = None,
    ) -> None:
        normalized_actor_id: Optional[UUID] = None
        if isinstance(actor_id, UUID):
            normalized_actor_id = actor_id
        elif isinstance(actor_id, str) and actor_id:
            try:
                normalized_actor_id = UUID(actor_id)
            except Exception:
                # игнорируем некорректный UUID, как в прежней реализации
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
