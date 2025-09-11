from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_log import log_admin_action


async def audit_log(
    db: AsyncSession,
    *,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    request: Any = None,
    reason: str | None = None,
    override: bool = False,
    extra: dict[str, Any] | None = None,
    node_type: str | None = None,
) -> None:
    payload: dict[str, Any] = extra.copy() if extra else {}
    await log_admin_action(
        db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
        override=override,
        reason=reason,
        **payload,
    )

    if node_type:
        event = None
        act = action.lower()
        if act.endswith("_create"):
            event = "create"
        elif act.endswith("_update"):
            event = "update"
        elif act.endswith("_publish"):
            event = "publish"
        elif "validate" in act:
            event = "validate"
        if event:
            rum_log = logging.getLogger("app.api.rum_metrics")
            rum_log.info(
                "RUM %s",
                {
                    "event": event,
                    "node_type": node_type,
                },
            )
