from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from domains.platform.audit.application.facade import AuditLogPayload, safe_audit_log

logger = logging.getLogger("domains.product.nodes.admin_activity")


@dataclass(slots=True)
class AdminEvent:
    event: str | None
    payload: dict[str, Any] | None = None
    key: str | None = None
    context: dict[str, Any] | None = None


def _merge(base: dict[str, Any] | None, extra: dict[str, Any] | None) -> dict[str, Any]:
    data: dict[str, Any] = dict(base or {})
    if extra:
        for key, value in extra.items():
            if value is None:
                continue
            data[key] = value
    return data


def make_event_payload(
    *,
    node_id: Any | None = None,
    comment_id: Any | None = None,
    base: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _merge(base, extra)
    if node_id is not None:
        payload.setdefault("node_id", node_id)
    if comment_id is not None:
        payload.setdefault("comment_id", comment_id)
    return payload


def make_event_context(
    *,
    node_id: Any | None = None,
    comment_id: Any | None = None,
    source: str | None = None,
    base: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = _merge(base, extra)
    if node_id is not None:
        context.setdefault("node_id", node_id)
    if comment_id is not None:
        context.setdefault("comment_id", comment_id)
    if source:
        context.setdefault("source", source)
    return context


async def emit_admin_activity(
    container,
    *,
    event: AdminEvent | None = None,
    audit: AuditLogPayload | None = None,
    suppressed: Iterable[type[Exception]] | None = None,
    log: logging.Logger | None = None,
) -> None:
    """Send admin activity event and optional audit log using container wiring."""

    activity_logger = log or logger
    if event and event.event and event.payload is not None:
        nodes_service = getattr(container, "nodes_service", None)
        safe_publish = (
            getattr(nodes_service, "_safe_publish", None) if nodes_service else None
        )
        context_payload = {"source": "nodes_admin_api"}
        if event.context:
            context_payload.update(event.context)
        if callable(safe_publish):
            safe_publish(
                event.event, event.payload, key=event.key, context=context_payload
            )
        else:
            try:
                container.events.publish(event.event, event.payload, key=event.key)
            except Exception as exc:  # noqa: BLE001
                activity_logger.warning(
                    "nodes_admin_event_publish_failed",
                    extra={
                        "event": event.event,
                        "key": event.key,
                        "context": context_payload,
                    },
                    exc_info=exc,
                )
    if audit:
        audit_container = getattr(container, "audit", None)
        audit_service = (
            getattr(audit_container, "service", None) if audit_container else None
        )
        await safe_audit_log(
            audit_service,
            audit,
            logger=activity_logger,
            error_slug="nodes_admin_audit_failed",
            suppressed=suppressed,
            log_extra={
                "action": audit.action,
                "resource_id": audit.resource_id,
            },
        )


__all__ = [
    "AdminEvent",
    "emit_admin_activity",
    "make_event_context",
    "make_event_payload",
]
