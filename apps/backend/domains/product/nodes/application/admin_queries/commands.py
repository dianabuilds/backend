"""Command-side utilities for admin node flows."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from domains.platform.audit.application.facade import AuditLogPayload
from domains.product.nodes.infrastructure import (
    AdminEvent,
    emit_admin_activity,
    make_event_context,
    make_event_payload,
)

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
    event: AdminEvent | None = None,
    audit: AuditLogPayload | None = None,
    suppressed: Iterable[type[Exception]] | None = None,
) -> None:
    await emit_admin_activity(
        container,
        event=event,
        audit=audit,
        suppressed=suppressed,
        log=logger,
    )


__all__ = [
    "SYSTEM_ACTOR_ID",
    "_emit_admin_activity",
    "_extract_actor_id",
    "logger",
    "AuditLogPayload",
    "AdminEvent",
    "make_event_context",
    "make_event_payload",
]
