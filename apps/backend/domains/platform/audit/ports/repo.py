from __future__ import annotations

from typing import Protocol

from domains.platform.audit.domain.audit import AuditEntry


class AuditLogRepository(Protocol):
    async def add(self, entry: AuditEntry) -> None: ...

    async def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        actions: list[str] | None = None,
        actor_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        resource_types: list[str] | None = None,
        modules: list[str] | None = None,
        search: str | None = None,
    ) -> list[dict]: ...


__all__ = ["AuditLogRepository"]
