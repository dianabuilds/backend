from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict

from ...domain.dtos import SanctionStatus
from ..common import isoformat_utc
from .presenter import build_decision_response
from .repository import AppealsRepository

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService


class AppealSnapshot(TypedDict):
    status: str
    decided_at: datetime | None
    decided_by: str | None
    decision_reason: str | None
    meta: dict[str, Any]


async def decide_appeal(
    service: PlatformModerationService,
    appeal_id: str,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
    repository: AppealsRepository | None = None,
) -> dict[str, Any]:
    async with service._lock:
        appeal = service._appeals.get(appeal_id)
        if not appeal:
            raise KeyError(appeal_id)
        result = str(body.get("result", "approved")).lower()
        appeal.status = result
        appeal.decision_reason = body.get("reason")
        appeal.decided_by = actor_id or body.get("decided_by") or "system"
        appeal.decided_at = service._now()
        appeal.meta.setdefault("history", []).append(
            {
                "actor": appeal.decided_by,
                "result": result,
                "reason": appeal.decision_reason,
                "decided_at": isoformat_utc(appeal.decided_at),
            }
        )
        if result == "approved":
            sanction = service._sanctions.get(appeal.target_id)
            if sanction:
                sanction.status = SanctionStatus.canceled
                sanction.revoked_at = appeal.decided_at
                sanction.revoked_by = appeal.decided_by
        status_value = str(appeal.status)
        decided_at_value = appeal.decided_at
        decided_by_value = appeal.decided_by
        decision_reason_value = appeal.decision_reason
        meta_value: dict[str, Any] = dict(appeal.meta)
        snapshot: AppealSnapshot = {
            "status": status_value,
            "decided_at": decided_at_value,
            "decided_by": decided_by_value,
            "decision_reason": decision_reason_value,
            "meta": meta_value,
        }

    db_record = None
    if repository is not None:
        db_record = await repository.record_decision(
            appeal_id,
            status=status_value,
            decided_at=decided_at_value,
            decided_by=decided_by_value,
            decision_reason=decision_reason_value,
            meta=meta_value,
        )

    decided_at_text = isoformat_utc(decided_at_value) or ""
    decided_by = decided_by_value or ""
    return build_decision_response(
        appeal_id,
        status=snapshot["status"],
        decided_at=decided_at_text,
        decided_by=decided_by,
        db_record=db_record,
    )


__all__ = ["decide_appeal"]
