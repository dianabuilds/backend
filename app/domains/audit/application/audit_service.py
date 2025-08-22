from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Временный фасад: используем legacy-реализацию, сохраняя доменную точку импорта
from app.services.audit import audit_log as _legacy_audit_log


async def audit_log(
    db: AsyncSession,
    *,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    before: Optional[dict[str, Any]] = None,
    after: Optional[dict[str, Any]] = None,
    request: Any = None,
    reason: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    await _legacy_audit_log(
        db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
        request=request,
        reason=reason,
        extra=extra,
    )
