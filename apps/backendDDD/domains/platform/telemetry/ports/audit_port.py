from __future__ import annotations

from typing import Protocol

from apps.backendDDD.domains.platform.telemetry.domain.audit import AuditEntry


class IAuditLogRepository(Protocol):
    async def add(self, entry: AuditEntry) -> None: ...


__all__ = ["IAuditLogRepository"]
