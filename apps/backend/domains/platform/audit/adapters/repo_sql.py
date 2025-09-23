from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.audit.domain.audit import AuditEntry
from domains.platform.audit.ports.repo import AuditLogRepository


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
            # Retention: keep only last 30 days
            try:
                await conn.execute(
                    text("DELETE FROM audit_logs WHERE created_at < now() - interval '30 days'")
                )
            except Exception:
                # Best-effort; ignore retention failures
                pass

    async def list(
        self,
        limit: int = 100,
        actions: list[str] | None = None,
        actor_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        base = (
            "SELECT id, actor_id, action, resource_type, resource_id, workspace_id, before, after, override, reason, ip, user_agent, created_at, extra "
            "FROM audit_logs"
        )
        where: list[str] = []
        params: dict[str, Any] = {"limit": int(limit)}
        if actions:
            # Normalize to lowercase strings
            acts = [str(a).strip() for a in actions if a and str(a).strip()]
            if acts:
                conds = []
                for idx, a in enumerate(acts):
                    key = f"act_{idx}"
                    conds.append(f"action = :{key}")
                    params[key] = a
                where.append("(" + " OR ".join(conds) + ")")
        if actor_id:
            where.append("actor_id = :actor_id")
            params["actor_id"] = str(actor_id)
        if date_from:
            where.append("created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            where.append("created_at <= :date_to")
            params["date_to"] = date_to
        if where:
            base += " WHERE " + " AND ".join(where)
        base += " ORDER BY created_at DESC LIMIT :limit"
        sql = text(base)
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, params)
            rows = res.mappings().all()
            return [dict(r) for r in rows]


__all__ = ["SQLAuditRepo"]
