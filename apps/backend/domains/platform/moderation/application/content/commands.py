from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...domain.dtos import ContentStatus
from ..common import isoformat_utc
from .presenter import DecisionResponse, build_decision_response
from .repository import ContentRepository

if TYPE_CHECKING:  # pragma: no cover
    from ..service import PlatformModerationService


async def decide_content(
    service: PlatformModerationService,
    content_id: str,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
    repository: ContentRepository | None = None,
) -> DecisionResponse:
    async with service._lock:
        content = service._content.get(content_id)
        if not content:
            raise KeyError(content_id)
        action = str(body.get("action", "keep")).lower()
        reason = body.get("reason")
        now = service._now()
        decision_entry = {
            "action": action,
            "reason": reason,
            "actor": actor_id or body.get("actor") or "system",
            "decided_at": isoformat_utc(now),
            "notes": body.get("notes"),
        }
        content.moderation_history.insert(0, decision_entry)
        if action in {"keep", "allow", "dismiss"}:
            content.status = ContentStatus.resolved
        elif action in {"hide", "delete", "remove"}:
            content.status = ContentStatus.hidden
        elif action in {"restrict", "limit"}:
            content.status = ContentStatus.restricted
        elif action in {"escalate", "review"}:
            content.status = ContentStatus.escalated
        content.meta["last_decision"] = decision_entry
        status_value = content.status.value

    db_record = None
    if repository is not None:
        db_record = await repository.record_decision(
            content_id,
            action=action,
            reason=reason,
            actor_id=actor_id,
            payload=body,
        )

    return build_decision_response(
        content_id,
        status=status_value,
        decision=decision_entry,
        db_record=db_record,
    )


async def edit_content(
    service: PlatformModerationService,
    content_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    async with service._lock:
        content = service._content.get(content_id)
        if not content:
            raise KeyError(content_id)
        update = dict(patch or {})
        if update:
            content.meta.update(update)
        return {"content_id": content_id, "meta": dict(content.meta)}
