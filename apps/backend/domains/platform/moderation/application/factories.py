from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..domain.dtos import (
    ContentStatus,
    ContentType,
    ReportStatus,
    SanctionStatus,
    SanctionType,
    TicketPriority,
    TicketStatus,
)
from ..domain.records import (
    AIRuleRecord,
    AppealRecord,
    ContentRecord,
    ModeratorNoteRecord,
    ReportRecord,
    SanctionRecord,
    TicketMessageRecord,
    TicketRecord,
    UserRecord,
)
from .common import generate_id as generate_id_value
from .common import isoformat_utc

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService


def create_user(
    service: PlatformModerationService,
    *,
    user_id: str,
    username: str,
    email: str | None,
    roles: Iterable[str],
    status: str,
    registered_at: datetime,
    last_seen_at: datetime | None = None,
    meta: dict[str, Any] | None = None,
) -> UserRecord:
    record = UserRecord(
        id=user_id,
        username=username,
        email=email,
        roles=list(dict.fromkeys(str(r) for r in roles)),
        status=status,
        registered_at=registered_at,
        last_seen_at=last_seen_at,
        meta=dict(meta or {}),
    )
    service._users[record.id] = record
    return record


def create_sanction(
    service: PlatformModerationService,
    user: UserRecord,
    *,
    stype: SanctionType,
    status: SanctionStatus,
    reason: str | None,
    issued_by: str | None,
    issued_at: datetime,
    starts_at: datetime,
    ends_at: datetime | None = None,
    evidence: Iterable[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> SanctionRecord:
    sanction = SanctionRecord(
        id=generate_id_value("san"),
        user_id=user.id,
        type=stype,
        status=status,
        reason=reason,
        issued_by=issued_by,
        issued_at=issued_at,
        starts_at=starts_at,
        ends_at=ends_at,
        evidence=list(evidence or []),
        meta=dict(meta or {}),
    )
    service._sanctions[sanction.id] = sanction
    user.sanction_ids.insert(0, sanction.id)
    if sanction.type == SanctionType.ban and sanction.status == SanctionStatus.active:
        user.status = "banned"
    return sanction


def create_note(
    service: PlatformModerationService,
    user: UserRecord,
    *,
    text: str,
    author_id: str | None,
    author_name: str | None,
    pinned: bool = False,
    created_at: datetime | None = None,
    meta: dict[str, Any] | None = None,
) -> ModeratorNoteRecord:
    note = ModeratorNoteRecord(
        id=generate_id_value("note"),
        user_id=user.id,
        text=text,
        created_at=created_at or service._now(),
        author_id=author_id,
        author_name=author_name,
        pinned=pinned,
        meta=dict(meta or {}),
    )
    service._notes[note.id] = note
    user.note_ids.insert(0, note.id)
    return note


def create_content(
    service: PlatformModerationService,
    *,
    content_id: str | None,
    content_type: ContentType,
    author_id: str,
    created_at: datetime,
    preview: str | None = None,
    ai_labels: Iterable[str] | None = None,
    status: ContentStatus = ContentStatus.pending,
    meta: dict[str, Any] | None = None,
) -> ContentRecord:
    cid = content_id or generate_id_value("content")
    record = ContentRecord(
        id=cid,
        content_type=content_type,
        author_id=author_id,
        created_at=created_at,
        preview=preview,
        ai_labels=list(ai_labels or []),
        status=status,
        meta=dict(meta or {}),
    )
    service._content[record.id] = record
    return record


def create_report(
    service: PlatformModerationService,
    *,
    content: ContentRecord,
    reporter_id: str,
    category: str,
    text: str | None,
    status: ReportStatus = ReportStatus.new,
    created_at: datetime | None = None,
    source: str | None = None,
    notes: str | None = None,
    meta: dict[str, Any] | None = None,
) -> ReportRecord:
    report = ReportRecord(
        id=generate_id_value("rep"),
        object_type=content.content_type.value,
        object_id=content.id,
        reporter_id=reporter_id,
        category=category,
        text=text,
        status=status,
        source=source,
        created_at=created_at or service._now(),
        notes=notes,
        meta=dict(meta or {}),
    )
    service._reports[report.id] = report
    content.report_ids.insert(0, report.id)
    subject = service._users.get(content.author_id)
    if subject:
        subject.report_ids.insert(0, report.id)
    return report


def create_ticket(
    service: PlatformModerationService,
    *,
    title: str,
    author_id: str,
    priority: TicketPriority,
    assignee_id: str | None,
    status: TicketStatus,
    created_at: datetime,
    meta: dict[str, Any] | None = None,
) -> TicketRecord:
    ticket = TicketRecord(
        id=generate_id_value("tic"),
        title=title,
        priority=priority,
        author_id=author_id,
        assignee_id=assignee_id,
        status=status,
        created_at=created_at,
        updated_at=created_at,
        meta=dict(meta or {}),
    )
    service._tickets[ticket.id] = ticket
    user = service._users.get(author_id)
    if user:
        user.ticket_ids.insert(0, ticket.id)
    return ticket


def create_ticket_message(
    service: PlatformModerationService,
    ticket: TicketRecord,
    *,
    author_id: str,
    text: str,
    author_name: str | None = None,
    internal: bool = False,
    created_at: datetime | None = None,
    attachments: Iterable[dict[str, Any]] | None = None,
) -> TicketMessageRecord:
    message = TicketMessageRecord(
        id=generate_id_value("msg"),
        ticket_id=ticket.id,
        author_id=author_id,
        text=text,
        attachments=[dict(a) for a in attachments or []],
        internal=internal,
        author_name=author_name,
        created_at=created_at or service._now(),
    )
    service._ticket_messages[message.id] = message
    ticket.message_ids.append(message.id)
    ticket.last_message_at = message.created_at
    ticket.updated_at = message.created_at
    return message


def create_appeal(
    service: PlatformModerationService,
    *,
    sanction: SanctionRecord,
    user_id: str,
    text: str,
    status: str = "new",
    created_at: datetime | None = None,
) -> AppealRecord:
    appeal = AppealRecord(
        id=generate_id_value("apl"),
        target_type="sanction",
        target_id=sanction.id,
        user_id=user_id,
        text=text,
        status=status,
        created_at=created_at or service._now(),
    )
    service._appeals[appeal.id] = appeal
    sanction.meta.setdefault("appeal_ids", []).append(appeal.id)
    return appeal


def create_ai_rule(
    service: PlatformModerationService,
    *,
    category: str,
    thresholds: dict[str, Any],
    actions: dict[str, Any],
    enabled: bool,
    updated_by: str,
    description: str | None = None,
    updated_at: datetime | None = None,
) -> AIRuleRecord:
    rule = AIRuleRecord(
        id=generate_id_value("air"),
        category=category,
        thresholds=dict(thresholds),
        actions=dict(actions),
        enabled=enabled,
        updated_by=updated_by,
        updated_at=updated_at or service._now(),
        description=description,
        history=[],
    )
    rule.history.append(
        {
            "updated_at": isoformat_utc(rule.updated_at),
            "updated_by": updated_by,
            "changes": {
                "thresholds": dict(thresholds),
                "actions": dict(actions),
                "enabled": enabled,
            },
        }
    )
    service._ai_rules[rule.id] = rule
    return rule
