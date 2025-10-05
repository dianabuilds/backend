from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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

IsoFunc = Callable[[datetime | None], str | None]
ParseFunc = Callable[[Any], datetime | None]
NowFunc = Callable[[], datetime]


@dataclass(slots=True)
class ModerationSnapshot:
    """Aggregate moderation state that can be persisted and restored."""

    users: dict[str, UserRecord]
    sanctions: dict[str, SanctionRecord]
    notes: dict[str, ModeratorNoteRecord]
    reports: dict[str, ReportRecord]
    content: dict[str, ContentRecord]
    tickets: dict[str, TicketRecord]
    ticket_messages: dict[str, TicketMessageRecord]
    appeals: dict[str, AppealRecord]
    ai_rules: dict[str, AIRuleRecord]
    idempotency: dict[str, str]


class ModerationSnapshotCodec:
    """Serialize and deserialize moderation state for storage backends."""

    def __init__(
        self, *, isoformat: IsoFunc, parse_datetime: ParseFunc, now_factory: NowFunc
    ) -> None:
        self._iso = isoformat
        self._parse_datetime = parse_datetime
        self._now = now_factory

    def dump(self, snapshot: ModerationSnapshot) -> dict[str, Any]:
        return {
            "users": {
                uid: _serialize_user(record, self._iso)
                for uid, record in snapshot.users.items()
            },
            "sanctions": {
                sid: _serialize_sanction(record, self._iso)
                for sid, record in snapshot.sanctions.items()
            },
            "notes": {
                nid: _serialize_note(record, self._iso)
                for nid, record in snapshot.notes.items()
            },
            "reports": {
                rid: _serialize_report(record, self._iso)
                for rid, record in snapshot.reports.items()
            },
            "content": {
                cid: _serialize_content(record, self._iso)
                for cid, record in snapshot.content.items()
            },
            "tickets": {
                tid: _serialize_ticket(record, self._iso)
                for tid, record in snapshot.tickets.items()
            },
            "ticket_messages": {
                mid: _serialize_ticket_message(record, self._iso)
                for mid, record in snapshot.ticket_messages.items()
            },
            "appeals": {
                aid: _serialize_appeal(record, self._iso)
                for aid, record in snapshot.appeals.items()
            },
            "ai_rules": {
                rid: _serialize_rule(record, self._iso)
                for rid, record in snapshot.ai_rules.items()
            },
            "idempotency": dict(snapshot.idempotency),
        }

    def load(self, payload: Mapping[str, Any]) -> ModerationSnapshot:
        users = {
            uid: _deserialize_user(data, self._parse_datetime, self._now)
            for uid, data in payload.get("users", {}).items()
        }
        sanctions = {
            sid: _deserialize_sanction(data, self._parse_datetime, self._now)
            for sid, data in payload.get("sanctions", {}).items()
        }
        notes = {
            nid: _deserialize_note(data, self._parse_datetime, self._now)
            for nid, data in payload.get("notes", {}).items()
        }
        reports = {
            rid: _deserialize_report(data, self._parse_datetime)
            for rid, data in payload.get("reports", {}).items()
        }
        content = {
            cid: _deserialize_content(data, self._parse_datetime, self._now)
            for cid, data in payload.get("content", {}).items()
        }
        tickets = {
            tid: _deserialize_ticket(data, self._parse_datetime)
            for tid, data in payload.get("tickets", {}).items()
        }
        ticket_messages = {
            mid: _deserialize_ticket_message(data, self._parse_datetime)
            for mid, data in payload.get("ticket_messages", {}).items()
        }
        appeals = {
            aid: _deserialize_appeal(data, self._parse_datetime)
            for aid, data in payload.get("appeals", {}).items()
        }
        ai_rules = {
            rid: _deserialize_rule(data, self._parse_datetime)
            for rid, data in payload.get("ai_rules", {}).items()
        }
        idempotency = {
            str(key): str(value)
            for key, value in payload.get("idempotency", {}).items()
        }
        return ModerationSnapshot(
            users=users,
            sanctions=sanctions,
            notes=notes,
            reports=reports,
            content=content,
            tickets=tickets,
            ticket_messages=ticket_messages,
            appeals=appeals,
            ai_rules=ai_rules,
            idempotency=idempotency,
        )


def _serialize_user(record: UserRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "username": record.username,
        "email": record.email,
        "roles": list(record.roles),
        "status": record.status,
        "registered_at": iso(record.registered_at),
        "last_seen_at": iso(record.last_seen_at),
        "meta": dict(record.meta),
        "sanction_ids": list(record.sanction_ids),
        "note_ids": list(record.note_ids),
        "report_ids": list(record.report_ids),
        "ticket_ids": list(record.ticket_ids),
    }


def _serialize_sanction(record: SanctionRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "user_id": record.user_id,
        "type": record.type.value,
        "status": record.status.value,
        "reason": record.reason,
        "issued_by": record.issued_by,
        "issued_at": iso(record.issued_at),
        "starts_at": iso(record.starts_at),
        "ends_at": iso(record.ends_at),
        "evidence": list(record.evidence),
        "meta": dict(record.meta),
        "revoked_at": iso(record.revoked_at),
        "revoked_by": record.revoked_by,
    }


def _serialize_note(record: ModeratorNoteRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "user_id": record.user_id,
        "text": record.text,
        "created_at": iso(record.created_at),
        "author_id": record.author_id,
        "author_name": record.author_name,
        "pinned": record.pinned,
        "meta": dict(record.meta),
    }


def _serialize_report(record: ReportRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "object_type": record.object_type,
        "object_id": record.object_id,
        "reporter_id": record.reporter_id,
        "category": record.category,
        "text": record.text,
        "status": record.status.value,
        "source": record.source,
        "created_at": iso(record.created_at),
        "resolved_at": iso(record.resolved_at),
        "decision": record.decision,
        "notes": record.notes,
        "updates": list(record.updates),
        "meta": dict(record.meta),
    }


def _serialize_content(record: ContentRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "content_type": record.content_type.value,
        "author_id": record.author_id,
        "created_at": iso(record.created_at),
        "preview": record.preview,
        "ai_labels": list(record.ai_labels),
        "status": record.status.value,
        "report_ids": list(record.report_ids),
        "moderation_history": list(record.moderation_history),
        "meta": dict(record.meta),
    }


def _serialize_ticket(record: TicketRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "title": record.title,
        "priority": record.priority.value,
        "author_id": record.author_id,
        "assignee_id": record.assignee_id,
        "status": record.status.value,
        "created_at": iso(record.created_at),
        "updated_at": iso(record.updated_at),
        "last_message_at": iso(record.last_message_at),
        "unread_count": record.unread_count,
        "message_ids": list(record.message_ids),
        "meta": dict(record.meta),
    }


def _serialize_ticket_message(
    record: TicketMessageRecord, iso: IsoFunc
) -> dict[str, Any]:
    return {
        "id": record.id,
        "ticket_id": record.ticket_id,
        "author_id": record.author_id,
        "text": record.text,
        "attachments": list(record.attachments),
        "internal": record.internal,
        "author_name": record.author_name,
        "created_at": iso(record.created_at),
    }


def _serialize_appeal(record: AppealRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "target_type": record.target_type,
        "target_id": record.target_id,
        "user_id": record.user_id,
        "text": record.text,
        "status": record.status,
        "created_at": iso(record.created_at),
        "decided_at": iso(record.decided_at),
        "decided_by": record.decided_by,
        "decision_reason": record.decision_reason,
        "meta": dict(record.meta),
    }


def _serialize_rule(record: AIRuleRecord, iso: IsoFunc) -> dict[str, Any]:
    return {
        "id": record.id,
        "category": record.category,
        "thresholds": dict(record.thresholds),
        "actions": dict(record.actions),
        "enabled": record.enabled,
        "updated_by": record.updated_by,
        "updated_at": iso(record.updated_at),
        "description": record.description,
        "history": list(record.history),
    }


def _deserialize_user(
    data: Mapping[str, Any], parse_datetime: ParseFunc, now_factory: NowFunc
) -> UserRecord:
    return UserRecord(
        id=str(data.get("id")),
        username=str(data.get("username")),
        email=data.get("email"),
        roles=list(data.get("roles", [])),
        status=str(data.get("status")),
        registered_at=parse_datetime(data.get("registered_at")) or now_factory(),
        last_seen_at=parse_datetime(data.get("last_seen_at")),
        meta=dict(data.get("meta", {})),
        sanction_ids=list(data.get("sanction_ids", [])),
        note_ids=list(data.get("note_ids", [])),
        report_ids=list(data.get("report_ids", [])),
        ticket_ids=list(data.get("ticket_ids", [])),
    )


def _deserialize_sanction(
    data: Mapping[str, Any], parse_datetime: ParseFunc, now_factory: NowFunc
) -> SanctionRecord:
    return SanctionRecord(
        id=str(data.get("id")),
        user_id=str(data.get("user_id")),
        type=SanctionType(str(data.get("type", SanctionType.mute.value))),
        status=SanctionStatus(str(data.get("status", SanctionStatus.active.value))),
        reason=data.get("reason"),
        issued_by=data.get("issued_by"),
        issued_at=parse_datetime(data.get("issued_at")) or now_factory(),
        starts_at=parse_datetime(data.get("starts_at")) or now_factory(),
        ends_at=parse_datetime(data.get("ends_at")),
        evidence=list(data.get("evidence", [])),
        meta=dict(data.get("meta", {})),
        revoked_at=parse_datetime(data.get("revoked_at")),
        revoked_by=data.get("revoked_by"),
    )


def _deserialize_note(
    data: Mapping[str, Any], parse_datetime: ParseFunc, now_factory: NowFunc
) -> ModeratorNoteRecord:
    return ModeratorNoteRecord(
        id=str(data.get("id")),
        user_id=str(data.get("user_id")),
        text=str(data.get("text", "")),
        created_at=parse_datetime(data.get("created_at")) or now_factory(),
        author_id=data.get("author_id"),
        author_name=data.get("author_name"),
        pinned=bool(data.get("pinned", False)),
        meta=dict(data.get("meta", {})),
    )


def _deserialize_report(
    data: Mapping[str, Any], parse_datetime: ParseFunc
) -> ReportRecord:
    return ReportRecord(
        id=str(data.get("id")),
        object_type=str(data.get("object_type", "unknown")),
        object_id=str(data.get("object_id", "")),
        reporter_id=str(data.get("reporter_id", "")),
        category=str(data.get("category", "")),
        text=data.get("text"),
        status=ReportStatus(str(data.get("status", ReportStatus.new.value))),
        source=data.get("source"),
        created_at=parse_datetime(data.get("created_at")),
        resolved_at=parse_datetime(data.get("resolved_at")),
        decision=data.get("decision"),
        notes=data.get("notes"),
        updates=list(data.get("updates", [])),
        meta=dict(data.get("meta", {})),
    )


def _deserialize_content(
    data: Mapping[str, Any], parse_datetime: ParseFunc, now_factory: NowFunc
) -> ContentRecord:
    return ContentRecord(
        id=str(data.get("id")),
        content_type=ContentType(str(data.get("content_type", ContentType.node.value))),
        author_id=str(data.get("author_id", "")),
        created_at=parse_datetime(data.get("created_at")) or now_factory(),
        preview=data.get("preview"),
        ai_labels=list(data.get("ai_labels", [])),
        status=ContentStatus(str(data.get("status", ContentStatus.pending.value))),
        report_ids=list(data.get("report_ids", [])),
        moderation_history=list(data.get("moderation_history", [])),
        meta=dict(data.get("meta", {})),
    )


def _deserialize_ticket(
    data: Mapping[str, Any], parse_datetime: ParseFunc
) -> TicketRecord:
    return TicketRecord(
        id=str(data.get("id")),
        title=str(data.get("title", "")),
        priority=TicketPriority(str(data.get("priority", TicketPriority.normal.value))),
        author_id=str(data.get("author_id", "")),
        assignee_id=data.get("assignee_id"),
        status=TicketStatus(str(data.get("status", TicketStatus.new.value))),
        created_at=parse_datetime(data.get("created_at")),
        updated_at=parse_datetime(data.get("updated_at")),
        last_message_at=parse_datetime(data.get("last_message_at")),
        unread_count=int(data.get("unread_count", 0)),
        message_ids=list(data.get("message_ids", [])),
        meta=dict(data.get("meta", {})),
    )


def _deserialize_ticket_message(
    data: Mapping[str, Any], parse_datetime: ParseFunc
) -> TicketMessageRecord:
    return TicketMessageRecord(
        id=str(data.get("id")),
        ticket_id=str(data.get("ticket_id", "")),
        author_id=str(data.get("author_id", "")),
        text=str(data.get("text", "")),
        attachments=list(data.get("attachments", [])),
        internal=bool(data.get("internal", False)),
        author_name=data.get("author_name"),
        created_at=parse_datetime(data.get("created_at")),
    )


def _deserialize_appeal(
    data: Mapping[str, Any], parse_datetime: ParseFunc
) -> AppealRecord:
    return AppealRecord(
        id=str(data.get("id")),
        target_type=str(data.get("target_type", "")),
        target_id=str(data.get("target_id", "")),
        user_id=str(data.get("user_id", "")),
        text=data.get("text"),
        status=str(data.get("status", "new")),
        created_at=parse_datetime(data.get("created_at")),
        decided_at=parse_datetime(data.get("decided_at")),
        decided_by=data.get("decided_by"),
        decision_reason=data.get("decision_reason"),
        meta=dict(data.get("meta", {})),
    )


def _deserialize_rule(
    data: Mapping[str, Any], parse_datetime: ParseFunc
) -> AIRuleRecord:
    return AIRuleRecord(
        id=str(data.get("id")),
        category=str(data.get("category", "default")),
        thresholds=dict(data.get("thresholds", {})),
        actions=dict(data.get("actions", {})),
        enabled=bool(data.get("enabled", True)),
        updated_by=data.get("updated_by"),
        updated_at=parse_datetime(data.get("updated_at")),
        description=data.get("description"),
        history=list(data.get("history", [])),
    )


__all__ = ["ModerationSnapshot", "ModerationSnapshotCodec"]
