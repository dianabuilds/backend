from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_log import log_admin_action


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
    workspace_id: str | None = None,
    node_type: str | None = None,
) -> None:
    payload: dict[str, Any] = extra.copy() if extra else {}
    if reason:
        payload["reason"] = reason
    await log_admin_action(
        db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
        workspace_id=workspace_id,
        **payload,
    )

    if workspace_id and node_type:
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
                    "ws_id": workspace_id,
                    "node_type": node_type,
                },
            )
