from __future__ import annotations

from typing import Protocol

from domains.platform.audit.domain.audit import AuditEntry


class AuditLogRepository(Protocol):
    async def add(self, entry: AuditEntry) -> None: ...
    async def list(self, limit: int = 100) -> list[dict]: ...


__all__ = ["AuditLogRepository"]
