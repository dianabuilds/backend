from __future__ import annotations

import time

from domains.platform.audit.domain.audit import AuditEntry
from domains.platform.audit.ports.repo import AuditLogRepository


class InMemoryAuditRepo(AuditLogRepository):
    def __init__(self, max_items: int = 5000) -> None:
        self._max = max_items
        self._items: list[dict] = []

    async def add(self, entry: AuditEntry) -> None:
        row = {
            "ts": int(time.time() * 1000),
            "actor_id": str(entry.actor_id) if entry.actor_id else None,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "before": entry.before,
            "after": entry.after,
            "ip": entry.ip,
            "user_agent": entry.user_agent,
            "extra": entry.extra,
        }
        self._items.append(row)
        if len(self._items) > self._max:
            # drop oldest
            self._items = self._items[-self._max :]

    async def list(self, limit: int = 100) -> list[dict]:
        return list(reversed(self._items[-int(limit) :]))


__all__ = ["InMemoryAuditRepo"]
