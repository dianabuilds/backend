from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from ...domain.dtos import (
    AIRuleDTO,
    AppealDTO,
    ModeratorNoteDTO,
    ReportDTO,
    SanctionDTO,
    TicketDTO,
    TicketMessageDTO,
)
from ...domain.records import (
    AIRuleRecord,
    AppealRecord,
    ModeratorNoteRecord,
    ReportRecord,
    SanctionRecord,
    TicketMessageRecord,
    TicketRecord,
)

IsoFunc = Callable[[datetime | None], str | None]
Resolver = Callable[[str], TicketMessageRecord | None]


def sanction_to_dto(record: SanctionRecord, *, iso: IsoFunc) -> SanctionDTO:
    return SanctionDTO(
        id=record.id,
        type=record.type,
        status=record.status,
        reason=record.reason,
        issued_by=record.issued_by,
        issued_at=iso(record.issued_at),
        starts_at=iso(record.starts_at),
        ends_at=iso(record.ends_at),
        revoked_at=iso(record.revoked_at),
        revoked_by=record.revoked_by,
        evidence=list(record.evidence),
        meta=dict(record.meta),
    )


def note_to_dto(record: ModeratorNoteRecord, *, iso: IsoFunc) -> ModeratorNoteDTO:
    return ModeratorNoteDTO(
        id=record.id,
        text=record.text,
        author_id=record.author_id,
        author_name=record.author_name,
        created_at=iso(record.created_at),
        pinned=record.pinned,
        meta=dict(record.meta),
    )


def report_to_dto(record: ReportRecord, *, iso: IsoFunc) -> ReportDTO:
    return ReportDTO(
        id=record.id,
        object_type=record.object_type,
        object_id=record.object_id,
        reporter_id=record.reporter_id,
        category=record.category,
        text=record.text,
        status=record.status,
        created_at=iso(record.created_at),
        resolved_at=iso(record.resolved_at),
        decision=record.decision,
        notes=record.notes,
        updates=list(record.updates),
        source=record.source,
        meta=dict(record.meta),
    )


def ticket_message_to_dto(
    record: TicketMessageRecord, *, iso: IsoFunc
) -> TicketMessageDTO:
    return TicketMessageDTO(
        id=record.id,
        ticket_id=record.ticket_id,
        author_id=record.author_id,
        text=record.text,
        attachments=list(record.attachments),
        internal=record.internal,
        author_name=record.author_name,
        created_at=iso(record.created_at),
    )


def ticket_to_dto(
    record: TicketRecord,
    *,
    resolve_message: Resolver,
    iso: IsoFunc,
) -> TicketDTO:
    last_message_at = record.last_message_at
    if last_message_at is None and record.message_ids:
        last = resolve_message(record.message_ids[-1])
        if last and last.created_at:
            last_message_at = last.created_at
    return TicketDTO(
        id=record.id,
        title=record.title,
        priority=record.priority,
        author_id=record.author_id,
        assignee_id=record.assignee_id,
        status=record.status,
        created_at=iso(record.created_at),
        updated_at=iso(record.updated_at),
        last_message_at=iso(last_message_at),
        unread_count=int(record.unread_count),
        meta=dict(record.meta),
    )


def appeal_to_dto(record: AppealRecord, *, iso: IsoFunc) -> AppealDTO:
    return AppealDTO(
        id=record.id,
        target_type=record.target_type,
        target_id=record.target_id,
        user_id=record.user_id,
        text=record.text,
        status=record.status,
        created_at=iso(record.created_at),
        decided_at=iso(record.decided_at),
        decided_by=record.decided_by,
        decision_reason=record.decision_reason,
        meta=dict(record.meta),
    )


def ai_rule_to_dto(record: AIRuleRecord, *, iso: IsoFunc) -> AIRuleDTO:
    return AIRuleDTO(
        id=record.id,
        category=record.category,
        thresholds=dict(record.thresholds),
        actions=dict(record.actions),
        enabled=record.enabled,
        updated_by=record.updated_by,
        updated_at=iso(record.updated_at),
        description=record.description,
        history=list(record.history),
    )


__all__ = [
    "ai_rule_to_dto",
    "appeal_to_dto",
    "note_to_dto",
    "report_to_dto",
    "sanction_to_dto",
    "ticket_message_to_dto",
    "ticket_to_dto",
]
