from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import TYPE_CHECKING

from ..domain.dtos import (
    CardAction,
    CardDTO,
    ContentStatus,
    OverviewDTO,
    ReportStatus,
    SanctionStatus,
    TicketStatus,
)
from .common import resolve_iso
from .presenters.dto_builders import sanction_to_dto
from .users import user_to_summary

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from .service import PlatformModerationService


async def get_overview(
    service: PlatformModerationService, limit: int = 10
) -> OverviewDTO:
    async with service._lock:
        reports = list(service._reports.values())
        tickets = list(service._tickets.values())
        sanctions = sorted(
            service._sanctions.values(), key=lambda s: s.issued_at, reverse=True
        )
        content_items = list(service._content.values())
        appeals = list(service._appeals.values())

    complaints_new = {
        "count": sum(1 for r in reports if r.status == ReportStatus.new),
        "by_category": dict(Counter(r.category for r in reports)),
    }

    tickets_block = {
        "open": sum(
            1
            for t in tickets
            if t.status not in {TicketStatus.closed, TicketStatus.solved}
        ),
        "waiting": sum(1 for t in tickets if t.status == TicketStatus.waiting),
        "appeals_open": sum(
            1 for a in appeals if a.status.lower() in {"new", "pending", "review"}
        ),
    }

    content_counts: Counter[str] = Counter()
    for item in content_items:
        if item.status == ContentStatus.pending:
            content_counts[item.content_type.value] += 1

    iso = resolve_iso(service)
    last_sanctions = [sanction_to_dto(s, iso=iso) for s in sanctions[:limit]]

    complaint_sources = [
        {"label": source, "value": count}
        for source, count in Counter((r.source or "user") for r in reports).items()
    ]

    resolved_durations = [
        (r.resolved_at - r.created_at).total_seconds() / 3600.0
        for r in reports
        if r.created_at and r.resolved_at
    ]
    avg_response_time = mean(resolved_durations) if resolved_durations else None

    ai_decisions = 0
    total_decisions = 0
    for item in content_items:
        for history in item.moderation_history:
            total_decisions += 1
            actor = (history.get("actor") or "").lower()
            if "ai" in actor:
                ai_decisions += 1
    ai_share = float(ai_decisions) / float(total_decisions) if total_decisions else 0.0

    cards: list[CardDTO] = []
    flagged_users = [
        user_to_summary(service, service._users[s.user_id])
        for s in sanctions
        if s.status == SanctionStatus.active and s.user_id in service._users
    ]
    for user_summary in flagged_users[:3]:
        cards.append(
            CardDTO(
                type="user",
                id=user_summary.id,
                title=user_summary.username,
                subtitle=f"Active sanctions: {user_summary.sanction_count}",
                status=user_summary.status,
                meta=user_summary.meta,
                actions=[
                    CardAction(key="open_user", label="Open", kind="primary"),
                    CardAction(
                        key="lift_sanctions", label="Lift sanction", kind="danger"
                    ),
                ],
                roleVisibility=["Admin", "Moderator"],
            )
        )

    charts = {
        "complaint_sources": complaint_sources,
        "avg_response_time_hours": avg_response_time,
        "ai_autodecisions_share": ai_share,
    }

    return OverviewDTO(
        complaints_new=complaints_new,
        tickets=tickets_block,
        content_queues=dict(content_counts),
        last_sanctions=last_sanctions,
        charts=charts,
        cards=cards,
    )


__all__ = ["get_overview"]
