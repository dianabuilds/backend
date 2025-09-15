from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backendDDD.domains.platform.audit.domain.audit import AuditEntry
from apps.backendDDD.domains.platform.audit.ports.repo import AuditLogRepository


class SQLAuditRepo(AuditLogRepository):
    """Simple SQL repository for Postgres (async SQLAlchemy core).

    Expects a table `audit_logs` compatible with the legacy model.
    """

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def add(self, entry: AuditEntry) -> None:
        reason: str | None = None
        if isinstance(entry.extra, dict) and "reason" in entry.extra:
            try:
                reason = str(entry.extra.get("reason"))
            except Exception:
                reason = None
        sql = text(
            """
            INSERT INTO audit_logs(
              actor_id, action, resource_type, resource_id,
              workspace_id, before, after, override, reason, ip, user_agent, created_at, extra
            ) VALUES (
              :actor_id, :action, :resource_type, :resource_id,
              :workspace_id, cast(:before as jsonb), cast(:after as jsonb), :override, :reason, :ip, :user_agent, now(), cast(:extra as jsonb)
            )
            """
        )
        params: dict[str, Any] = {
            "actor_id": str(entry.actor_id) if entry.actor_id else None,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "workspace_id": None,
            "before": json.dumps(entry.before) if entry.before is not None else None,
            "after": json.dumps(entry.after) if entry.after is not None else None,
            "override": False,
            "reason": reason,
            "ip": entry.ip,
            "user_agent": entry.user_agent,
            "extra": json.dumps(entry.extra) if entry.extra is not None else None,
        }
        async with self._engine.begin() as conn:
            await conn.execute(sql, params)

    async def list(self, limit: int = 100) -> list[dict]:
        sql = text(
            "SELECT id, actor_id, action, resource_type, resource_id, workspace_id, before, after, override, reason, ip, user_agent, created_at, extra "
            "FROM audit_logs ORDER BY created_at DESC LIMIT :limit"
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, {"limit": int(limit)})
            rows = res.mappings().all()
            return [dict(r) for r in rows]


__all__ = ["SQLAuditRepo"]
