from __future__ import annotations

import time

from domains.platform.audit.domain.audit import AuditEntry
from domains.platform.audit.ports.repo import AuditLogRepository


class InMemoryAuditRepo(AuditLogRepository):
    def __init__(self, max_items: int = 5000) -> None:
        self._max = max_items
        self._items: list[dict] = []

    def _prune(self) -> None:
        # Keep at most 30 days of data and max_items cap
        now_ms = int(time.time() * 1000)
        keep_after = now_ms - 30 * 24 * 60 * 60 * 1000
        self._items = [it for it in self._items if int(it.get("ts", 0)) >= keep_after]
        if len(self._items) > self._max:
            self._items = self._items[-self._max :]

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
        self._prune()

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
    ) -> list[dict]:
        self._prune()
        data = list(self._items)
        if actions:
            aset = {a.strip().lower() for a in actions if a and str(a).strip()}
            if aset:
                data = [d for d in data if str(d.get("action", "")).lower() in aset]
        if actor_id:
            aid = str(actor_id)
            data = [d for d in data if str(d.get("actor_id")) == aid]

        def _parse_iso(s: str | None) -> int | None:
            if not s:
                return None
            try:
                from datetime import datetime

                if len(s) <= 10:
                    dt = datetime.fromisoformat(s)
                else:
                    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)
            except (ValueError, TypeError):
                return None

        start_ms = _parse_iso(date_from)
        end_ms = _parse_iso(date_to)
        if start_ms is not None:
            data = [d for d in data if int(d.get("ts", 0)) >= start_ms]
        if end_ms is not None:
            data = [d for d in data if int(d.get("ts", 0)) <= end_ms]

        if resource_types:
            rset = {str(r).strip().lower() for r in resource_types if r}
            if rset:
                data = [
                    d for d in data if str(d.get("resource_type", "")).lower() in rset
                ]
        if modules:
            mset = {str(m).strip().lower() for m in modules if m}
            if mset:
                data = [
                    d
                    for d in data
                    if str(d.get("action", "")).split(".", 1)[0].lower() in mset
                ]
        if search:
            needle = search.strip().lower()
            if needle:

                def _matches(row: dict) -> bool:
                    parts = [
                        str(row.get("action", "")),
                        str(row.get("resource_id", "")),
                        str(row.get("resource_type", "")),
                        str(row.get("actor_id", "")),
                        str(row.get("extra", "")),
                        str(row.get("ip", "")),
                        str(row.get("user_agent", "")),
                    ]
                    payload = " ".join(parts).lower()
                    return needle in payload

                data = [row for row in data if _matches(row)]

        data.sort(key=lambda d: int(d.get("ts", 0)), reverse=True)
        start = max(int(offset), 0)
        end = start + max(int(limit), 0)
        return data[start:end]


__all__ = ["InMemoryAuditRepo"]
