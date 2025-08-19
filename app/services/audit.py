from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def audit_log(
    db: AsyncSession,
    *,
    actor_id: Optional[str],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    before: Any = None,
    after: Any = None,
    reason: Optional[str] = None,
    request: Optional[Request] = None,
    extra: Any = None,
) -> None:
    ip = None
    ua = None
    if request is not None:
        try:
            ip = request.headers.get("x-forwarded-for") or request.client.host  # type: ignore[attr-defined]
        except Exception:
            ip = None
        ua = request.headers.get("user-agent")
    entry = AuditLog(
        actor_id=UUID(actor_id) if actor_id else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
        ip=ip,
        user_agent=ua,
        extra={"reason": reason} if reason else (extra or None),
    )
    db.add(entry)
    try:
        await db.flush()
    except Exception:
        # Не мешаем основному флоу
        pass
