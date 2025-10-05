from __future__ import annotations

from typing import TYPE_CHECKING

from ...domain.dtos import (
    SanctionStatus,
    TicketStatus,
    UserDetail,
    UserSummary,
)
from ...domain.records import UserRecord
from ..common import isoformat_utc, resolve_iso
from ..presenters.dto_builders import (
    note_to_dto,
    report_to_dto,
    sanction_to_dto,
    ticket_to_dto,
)
from ..sanctions import get_sanctions_for_user

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService


def user_to_summary(
    service: PlatformModerationService, record: UserRecord
) -> UserSummary:
    sanctions = get_sanctions_for_user(service, record)
    iso = resolve_iso(service)
    active_dtos = [
        sanction_to_dto(s, iso=iso)
        for s in sanctions
        if s.status == SanctionStatus.active
    ]
    last_dto = sanction_to_dto(sanctions[0], iso=iso) if sanctions else None
    open_tickets = sum(
        1
        for tid in record.ticket_ids
        if tid in service._tickets
        and service._tickets[tid].status
        not in {TicketStatus.solved, TicketStatus.closed}
    )
    appeals_active = sum(
        1
        for appeal in service._appeals.values()
        if appeal.user_id == record.id
        and appeal.status.lower() in {"new", "pending", "review"}
    )
    return UserSummary(
        id=record.id,
        username=record.username,
        email=record.email,
        roles=list(record.roles),
        status=record.status,
        registered_at=isoformat_utc(record.registered_at),
        last_seen_at=isoformat_utc(record.last_seen_at),
        complaints_count=len(record.report_ids),
        notes_count=len(record.note_ids),
        sanction_count=len(record.sanction_ids),
        active_sanctions=active_dtos,
        last_sanction=last_dto,
        meta={
            "tickets_open": open_tickets,
            "appeals_active": appeals_active,
        },
    )


def user_to_detail(
    service: PlatformModerationService, record: UserRecord
) -> UserDetail:
    base = user_to_summary(service, record)
    iso = resolve_iso(service)
    sanctions = [
        sanction_to_dto(s, iso=iso) for s in get_sanctions_for_user(service, record)
    ]
    reports = [
        report_to_dto(service._reports[rid], iso=iso)
        for rid in record.report_ids
        if rid in service._reports
    ]
    resolver = (
        service._ticket_messages.get
        if hasattr(service, "_ticket_messages")
        else (lambda _mid: None)
    )
    tickets = [
        ticket_to_dto(
            service._tickets[tid],
            resolve_message=resolver,
            iso=iso,
        )
        for tid in record.ticket_ids
        if tid in service._tickets
    ]
    notes = [
        note_to_dto(service._notes[nid], iso=iso)
        for nid in record.note_ids
        if nid in service._notes
    ]
    data = base.model_dump()
    data.update(
        {
            "sanctions": sanctions,
            "reports": reports,
            "tickets": tickets,
            "notes": notes,
        }
    )
    return UserDetail(**data)


__all__ = [
    "user_to_summary",
    "user_to_detail",
]
