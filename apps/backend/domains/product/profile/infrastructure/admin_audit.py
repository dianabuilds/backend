from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from domains.platform.audit.application.facade import AuditLogPayload, safe_audit_log

logger = logging.getLogger("domains.product.profile.admin")


async def log_profile_admin_action(
    container: Any,
    *,
    actor_id: str | None,
    action: str,
    target_user_id: str,
    request: Any | None = None,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Emit audit log entry describing admin profile action."""

    audit_container = getattr(container, "audit", None)
    audit_service = (
        getattr(audit_container, "service", None) if audit_container else None
    )
    if audit_service is None:
        return

    ip = None
    user_agent = None
    if request is not None:
        client = getattr(request, "client", None)
        ip = getattr(client, "host", None)
        headers = getattr(request, "headers", None)
        if headers:
            user_agent = headers.get("user-agent")

    payload = AuditLogPayload(
        actor_id=actor_id,
        action=action,
        resource_type="profile",
        resource_id=target_user_id,
        before=dict(before) if before else None,
        after=dict(after) if after else None,
        ip=ip,
        user_agent=user_agent,
        extra=dict(extra) if extra else None,
    )
    await safe_audit_log(
        audit_service,
        payload,
        logger=logger,
        error_slug="profile_admin_audit_failed",
        suppressed=(Exception,),
        log_extra={"action": action, "resource_id": target_user_id},
    )


def resolve_actor_id(
    claims: Mapping[str, Any] | None, request: Any | None = None
) -> str | None:
    """Return actor identifier prioritising subject claim, falling back to admin key."""

    if claims and claims.get("sub"):
        return str(claims["sub"])
    if request is not None:
        key = request.headers.get("X-Admin-Key") or request.headers.get("x-admin-key")
        if key:
            return "admin-key"
    return None


__all__ = ["log_profile_admin_action", "resolve_actor_id"]
