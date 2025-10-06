"""Command-side utilities for admin node flows."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("domains.product.nodes.application.admin_queries")

SYSTEM_ACTOR_ID = "00000000-0000-0000-0000-000000000000"


def _extract_actor_id(request: Any) -> str | None:
    try:
        ctx = getattr(request.state, "auth_context", None)
    except AttributeError:
        ctx = None
    if isinstance(ctx, dict):
        candidate = ctx.get("actor_id") or ctx.get("user_id") or ctx.get("sub")
        if candidate:
            return str(candidate)
    header_actor = request.headers.get("X-Actor-Id") or request.headers.get(
        "x-actor-id"
    )
    if header_actor:
        candidate = header_actor.strip()
        if candidate:
            return candidate
    return None


async def _emit_admin_activity(
    container,
    *,
    event: str | None = None,
    payload: dict[str, Any] | None = None,
    key: str | None = None,
    event_context: dict[str, Any] | None = None,
    audit_action: str | None = None,
    audit_actor: str | None = None,
    audit_resource_type: str | None = None,
    audit_resource_id: str | None = None,
    audit_reason: str | None = None,
    audit_extra: dict[str, Any] | None = None,
) -> None:
    if event and payload is not None:
        nodes_service = getattr(container, "nodes_service", None)
        safe_publish = (
            getattr(nodes_service, "_safe_publish", None) if nodes_service else None
        )
        context_payload: dict[str, Any] = {"source": "nodes_admin_api"}
        if event_context:
            context_payload.update(event_context)
        if callable(safe_publish):
            safe_publish(event, payload, key=key, context=context_payload)
        else:
            try:
                container.events.publish(event, payload, key=key)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "nodes_admin_event_publish_failed",
                    extra={"event": event, "key": key, "context": context_payload},
                    exc_info=exc,
                )
    if audit_action:
        audit_container = getattr(container, "audit", None)
        service = getattr(audit_container, "service", None) if audit_container else None
        log_fn = getattr(service, "log", None) if service else None
        if callable(log_fn):
            try:
                await log_fn(
                    actor_id=audit_actor,
                    action=audit_action,
                    resource_type=audit_resource_type,
                    resource_id=audit_resource_id,
                    reason=audit_reason,
                    extra=audit_extra,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "nodes_admin_audit_failed",
                    extra={"action": audit_action, "resource_id": audit_resource_id},
                    exc_info=exc,
                )


__all__ = ["SYSTEM_ACTOR_ID", "_emit_admin_activity", "_extract_actor_id", "logger"]
