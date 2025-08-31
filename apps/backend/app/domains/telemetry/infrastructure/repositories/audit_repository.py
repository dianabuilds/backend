from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.infrastructure.models.audit_log import AuditLog
from app.domains.telemetry.application.ports.audit_port import IAuditLogRepository
from app.domains.telemetry.domain.audit import AuditEntry


class AuditLogRepository(IAuditLogRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, entry: AuditEntry) -> None:
        model = AuditLog(
            actor_id=entry.actor_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            before=entry.before,
            after=entry.after,
            ip=entry.ip,
            user_agent=entry.user_agent,
            extra=entry.extra,
        )
        self._db.add(model)
        try:
            await self._db.flush()
        except Exception:
            # не мешаем основному флоу — поведение сохранено
            pass
