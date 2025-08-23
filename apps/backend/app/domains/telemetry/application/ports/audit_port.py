from __future__ import annotations

from typing import Protocol

from app.domains.telemetry.domain.audit import AuditEntry


class IAuditLogRepository(Protocol):
    async def add(self, entry: AuditEntry) -> None:  # pragma: no cover - контракт
        ...
