from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any
from uuid import uuid4

from .dtos import (
    AIRuleDTO,
    AppealDTO,
    CardAction,
    CardDTO,
    ContentStatus,
    ContentSummary,
    ContentType,
    ModeratorNoteDTO,
    OverviewDTO,
    ReportDTO,
    ReportStatus,
    SanctionDTO,
    SanctionStatus,
    SanctionType,
    TicketDTO,
    TicketMessageDTO,
    TicketPriority,
    TicketStatus,
    UserDetail,
    UserSummary,
)


@dataclass
class SanctionRecord:
    id: str
    user_id: str
    type: SanctionType
    status: SanctionStatus
    reason: str | None
    issued_by: str | None
    issued_at: datetime
    starts_at: datetime
    ends_at: datetime | None
    evidence: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    revoked_at: datetime | None = None
    revoked_by: str | None = None


@dataclass
class ModeratorNoteRecord:
    id: str
    user_id: str
    text: str
    created_at: datetime
    author_id: str | None
    author_name: str | None
    pinned: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportRecord:
    id: str
    object_type: str
    object_id: str
    reporter_id: str
    category: str
    text: str | None
    status: ReportStatus
    source: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    decision: str | None = None
    notes: str | None = None
    updates: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class TicketMessageRecord:
    id: str
    ticket_id: str
    author_id: str
    text: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    internal: bool = False
    author_name: str | None = None
    created_at: datetime | None = None


@dataclass
class TicketRecord:
    id: str
    title: str
    priority: TicketPriority
    author_id: str
    assignee_id: str | None = None
    status: TicketStatus = TicketStatus.new
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    message_ids: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppealRecord:
    id: str
    target_type: str
    target_id: str
    user_id: str
    text: str | None
    status: str = "new"
    created_at: datetime | None = None
    decided_at: datetime | None = None
    decided_by: str | None = None
    decision_reason: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIRuleRecord:
    id: str
    category: str
    thresholds: dict[str, Any] = field(default_factory=dict)
    actions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    updated_by: str | None = None
    updated_at: datetime | None = None
    description: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ContentRecord:
    id: str
    content_type: ContentType
    author_id: str
    created_at: datetime
    preview: str | None = None
    ai_labels: list[str] = field(default_factory=list)
    status: ContentStatus = ContentStatus.pending
    report_ids: list[str] = field(default_factory=list)
    moderation_history: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> ContentType:  # backwards compatibility
        return self.content_type

    @type.setter
    def type(self, value: ContentType) -> None:
        self.content_type = value


@dataclass
class UserRecord:
    id: str
    username: str
    email: str | None
    roles: list[str]
    status: str
    registered_at: datetime
    last_seen_at: datetime | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    sanction_ids: list[str] = field(default_factory=list)
    note_ids: list[str] = field(default_factory=list)
    report_ids: list[str] = field(default_factory=list)
    ticket_ids: list[str] = field(default_factory=list)


class PlatformModerationService:
    def __init__(self, *, seed_demo: bool = True):
        self._lock = asyncio.Lock()
        self._users: dict[str, UserRecord] = {}
        self._sanctions: dict[str, SanctionRecord] = {}
        self._notes: dict[str, ModeratorNoteRecord] = {}
        self._reports: dict[str, ReportRecord] = {}
        self._content: dict[str, ContentRecord] = {}
        self._tickets: dict[str, TicketRecord] = {}
        self._ticket_messages: dict[str, TicketMessageRecord] = {}
        self._appeals: dict[str, AppealRecord] = {}
        self._ai_rules: dict[str, AIRuleRecord] = {}
        self._idempotency: dict[str, str] = {}
        if seed_demo:
            self._seed_demo()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _iso(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                txt = str(value).strip()
                if not txt:
                    return None
                txt = txt.replace("Z", "+00:00")
                dt = datetime.fromisoformat(txt)
            except Exception:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:10]}"

    def _paginate(
        self, seq: Sequence[Any], limit: int, cursor: str | None
    ) -> tuple[list[Any], str | None]:
        limit = max(1, min(int(limit or 50), 200))
        offset = 0
        if cursor:
            try:
                offset = max(0, int(cursor))
            except Exception:
                offset = 0
        items = list(seq)
        chunk = items[offset : offset + limit]
        next_cursor = str(offset + limit) if offset + limit < len(items) else None
        return chunk, next_cursor

    # Ensure a minimal in?memory user exists for operations that attach to a user (e.g., sanctions/notes)
    async def ensure_user_stub(
        self, *, user_id: str, username: str, email: str | None = None
    ) -> None:
        async with self._lock:
            if user_id in self._users:
                return
            self._users[user_id] = UserRecord(
                id=user_id,
                username=username or user_id,
                email=email,
                roles=["User"],
                status="active",
                registered_at=self._now(),
            )

    async def warnings_count_recent(self, user_id: str, *, days: int = 10) -> int:
        """Count active warnings for `user_id` issued within the last `days`.

        In-memory implementation used by auto-ban logic.
        """
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                return 0
            since = self._now() - timedelta(days=int(days))
            cnt = 0
            for sid in user.sanction_ids:
                s = self._sanctions.get(sid)
                if not s:
                    continue
                if (
                    s.type == SanctionType.warning
                    and s.status == SanctionStatus.active
                    and s.issued_at >= since
                ):
                    cnt += 1
            return cnt

    def _get_sanctions_for_user(self, user: UserRecord) -> list[SanctionRecord]:
        return sorted(
            [
                self._sanctions[sid]
                for sid in user.sanction_ids
                if sid in self._sanctions
            ],
            key=lambda s: s.issued_at,
            reverse=True,
        )

    def _sanction_to_dto(self, sanction: SanctionRecord) -> SanctionDTO:
        return SanctionDTO(
            id=sanction.id,
            type=sanction.type,
            status=sanction.status,
            reason=sanction.reason,
            issued_by=sanction.issued_by,
            issued_at=self._iso(sanction.issued_at),
            starts_at=self._iso(sanction.starts_at),
            ends_at=self._iso(sanction.ends_at),
            revoked_at=self._iso(sanction.revoked_at),
            revoked_by=sanction.revoked_by,
            evidence=list(sanction.evidence),
            meta=dict(sanction.meta),
        )

    def _note_to_dto(self, note: ModeratorNoteRecord) -> ModeratorNoteDTO:
        return ModeratorNoteDTO(
            id=note.id,
            text=note.text,
            author_id=note.author_id,
            author_name=note.author_name,
            created_at=self._iso(note.created_at),
            pinned=note.pinned,
            meta=dict(note.meta),
        )

    def _report_to_dto(self, report: ReportRecord) -> ReportDTO:
        return ReportDTO(
            id=report.id,
            object_type=report.object_type,
            object_id=report.object_id,
            reporter_id=report.reporter_id,
            category=report.category,
            text=report.text,
            status=report.status,
            created_at=self._iso(report.created_at),
            resolved_at=self._iso(report.resolved_at),
            decision=report.decision,
            notes=report.notes,
            updates=list(report.updates),
            source=report.source,
            meta=dict(report.meta),
        )

    def _ticket_message_to_dto(self, message: TicketMessageRecord) -> TicketMessageDTO:
        return TicketMessageDTO(
            id=message.id,
            ticket_id=message.ticket_id,
            author_id=message.author_id,
            text=message.text,
            attachments=[dict(a) for a in message.attachments],
            internal=message.internal,
            author_name=message.author_name,
            created_at=self._iso(message.created_at),
        )

    def _ticket_to_dto(self, ticket: TicketRecord) -> TicketDTO:
        last_message_at = ticket.last_message_at
        if last_message_at is None and ticket.message_ids:
            last = self._ticket_messages.get(ticket.message_ids[-1])
            if last and last.created_at:
                last_message_at = last.created_at
        return TicketDTO(
            id=ticket.id,
            title=ticket.title,
            priority=ticket.priority,
            author_id=ticket.author_id,
            assignee_id=ticket.assignee_id,
            status=ticket.status,
            created_at=self._iso(ticket.created_at),
            updated_at=self._iso(ticket.updated_at),
            last_message_at=self._iso(last_message_at),
            unread_count=int(ticket.unread_count),
            meta=dict(ticket.meta),
        )

    def _appeal_to_dto(self, appeal: AppealRecord) -> AppealDTO:
        return AppealDTO(
            id=appeal.id,
            target_type=appeal.target_type,
            target_id=appeal.target_id,
            user_id=appeal.user_id,
            text=appeal.text,
            status=appeal.status,
            created_at=self._iso(appeal.created_at),
            decided_at=self._iso(appeal.decided_at),
            decided_by=appeal.decided_by,
            decision_reason=appeal.decision_reason,
            meta=dict(appeal.meta),
        )

    def _ai_rule_to_dto(self, rule: AIRuleRecord) -> AIRuleDTO:
        return AIRuleDTO(
            id=rule.id,
            category=rule.category,
            thresholds=dict(rule.thresholds),
            actions=dict(rule.actions),
            enabled=rule.enabled,
            updated_by=rule.updated_by,
            updated_at=self._iso(rule.updated_at),
            description=rule.description,
            history=list(rule.history),
        )

    def _content_to_summary(self, content: ContentRecord) -> ContentSummary:
        reports = [
            self._report_to_dto(self._reports[rid])
            for rid in content.report_ids
            if rid in self._reports
        ]
        return ContentSummary(
            id=content.id,
            type=content.content_type,
            author_id=content.author_id,
            created_at=self._iso(content.created_at),
            preview=content.preview,
            ai_labels=list(content.ai_labels),
            complaints_count=len(content.report_ids),
            status=content.status,
            moderation_history=list(content.moderation_history),
            reports=reports,
            meta=dict(content.meta),
        )

    def _user_to_summary(self, record: UserRecord) -> UserSummary:
        sanctions = self._get_sanctions_for_user(record)
        active_dtos = [
            self._sanction_to_dto(s)
            for s in sanctions
            if s.status == SanctionStatus.active
        ]
        last_dto = self._sanction_to_dto(sanctions[0]) if sanctions else None
        open_tickets = sum(
            1
            for tid in record.ticket_ids
            if tid in self._tickets
            and self._tickets[tid].status
            not in {TicketStatus.solved, TicketStatus.closed}
        )
        appeals_active = sum(
            1
            for appeal in self._appeals.values()
            if appeal.user_id == record.id
            and appeal.status.lower() in {"new", "pending", "review"}
        )
        return UserSummary(
            id=record.id,
            username=record.username,
            email=record.email,
            roles=list(record.roles),
            status=record.status,
            registered_at=self._iso(record.registered_at),
            last_seen_at=self._iso(record.last_seen_at),
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

    def _user_to_detail(self, record: UserRecord) -> UserDetail:
        base = self._user_to_summary(record)
        sanctions = [
            self._sanction_to_dto(s) for s in self._get_sanctions_for_user(record)
        ]
        reports = [
            self._report_to_dto(self._reports[rid])
            for rid in record.report_ids
            if rid in self._reports
        ]
        tickets = [
            self._ticket_to_dto(self._tickets[tid])
            for tid in record.ticket_ids
            if tid in self._tickets
        ]
        notes = [
            self._note_to_dto(self._notes[nid])
            for nid in record.note_ids
            if nid in self._notes
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

    def _create_user(
        self,
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
        self._users[record.id] = record
        return record

    def _create_sanction(
        self,
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
            id=self._generate_id("san"),
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
        self._sanctions[sanction.id] = sanction
        user.sanction_ids.insert(0, sanction.id)
        if (
            sanction.type == SanctionType.ban
            and sanction.status == SanctionStatus.active
        ):
            user.status = "banned"
        return sanction

    def _create_note(
        self,
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
            id=self._generate_id("note"),
            user_id=user.id,
            text=text,
            created_at=created_at or self._now(),
            author_id=author_id,
            author_name=author_name,
            pinned=pinned,
            meta=dict(meta or {}),
        )
        self._notes[note.id] = note
        user.note_ids.insert(0, note.id)
        return note

    def _create_content(
        self,
        *,
        content_id: str | None = None,
        content_type: ContentType,
        author_id: str,
        created_at: datetime,
        preview: str | None = None,
        ai_labels: Iterable[str] | None = None,
        status: ContentStatus = ContentStatus.pending,
        meta: dict[str, Any] | None = None,
    ) -> ContentRecord:
        cid = content_id or self._generate_id("content")
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
        self._content[record.id] = record
        return record

    def _create_report(
        self,
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
            id=self._generate_id("rep"),
            object_type=content.content_type.value,
            object_id=content.id,
            reporter_id=reporter_id,
            category=category,
            text=text,
            status=status,
            source=source,
            created_at=created_at or self._now(),
            notes=notes,
            meta=dict(meta or {}),
        )
        self._reports[report.id] = report
        content.report_ids.insert(0, report.id)
        subject = self._users.get(content.author_id)
        if subject:
            subject.report_ids.insert(0, report.id)
        return report

    def _create_ticket(
        self,
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
            id=self._generate_id("tic"),
            title=title,
            priority=priority,
            author_id=author_id,
            assignee_id=assignee_id,
            status=status,
            created_at=created_at,
            updated_at=created_at,
            meta=dict(meta or {}),
        )
        self._tickets[ticket.id] = ticket
        user = self._users.get(author_id)
        if user:
            user.ticket_ids.insert(0, ticket.id)
        return ticket

    def _create_ticket_message(
        self,
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
            id=self._generate_id("msg"),
            ticket_id=ticket.id,
            author_id=author_id,
            text=text,
            attachments=[dict(a) for a in attachments or []],
            internal=internal,
            author_name=author_name,
            created_at=created_at or self._now(),
        )
        self._ticket_messages[message.id] = message
        ticket.message_ids.append(message.id)
        ticket.last_message_at = message.created_at
        ticket.updated_at = message.created_at
        return message

    def _create_appeal(
        self,
        *,
        sanction: SanctionRecord,
        user_id: str,
        text: str,
        status: str = "new",
        created_at: datetime | None = None,
    ) -> AppealRecord:
        appeal = AppealRecord(
            id=self._generate_id("apl"),
            target_type="sanction",
            target_id=sanction.id,
            user_id=user_id,
            text=text,
            status=status,
            created_at=created_at or self._now(),
        )
        self._appeals[appeal.id] = appeal
        sanction.meta.setdefault("appeal_ids", []).append(appeal.id)
        return appeal

    def _create_ai_rule(
        self,
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
            id=self._generate_id("air"),
            category=category,
            thresholds=dict(thresholds),
            actions=dict(actions),
            enabled=enabled,
            updated_by=updated_by,
            updated_at=updated_at or self._now(),
            description=description,
            history=[],
        )
        rule.history.append(
            {
                "updated_at": self._iso(rule.updated_at),
                "updated_by": updated_by,
                "changes": {
                    "thresholds": dict(thresholds),
                    "actions": dict(actions),
                    "enabled": enabled,
                },
            }
        )
        self._ai_rules[rule.id] = rule
        return rule

    def _seed_demo(self) -> None:
        now = self._now()
        alice = self._create_user(
            user_id="u-100",
            username="alice",
            email="alice@example.com",
            roles=["User", "Moderator"],
            status="active",
            registered_at=now - timedelta(days=220),
            last_seen_at=now - timedelta(minutes=5),
            meta={"display_name": "Alice Wonderland"},
        )
        bob = self._create_user(
            user_id="u-101",
            username="bob",
            email="bob@example.com",
            roles=["User"],
            status="banned",
            registered_at=now - timedelta(days=420),
            last_seen_at=now - timedelta(days=60),
            meta={"display_name": "Bob Builder"},
        )
        charlie = self._create_user(
            user_id="u-102",
            username="charlie",
            email="charlie@example.com",
            roles=["User", "Editor"],
            status="active",
            registered_at=now - timedelta(days=180),
            last_seen_at=now - timedelta(hours=1),
            meta={"display_name": "Charlie"},
        )
        self._create_user(
            user_id="u-103",
            username="daria",
            email="daria@example.com",
            roles=["Admin"],
            status="active",
            registered_at=now - timedelta(days=500),
            last_seen_at=now - timedelta(minutes=15),
            meta={"display_name": "Daria"},
        )

        self._create_note(
            alice,
            text="Be careful with NSFW tags.",
            author_id="moderator:kate",
            author_name="Kate",
        )
        self._create_note(
            bob,
            text="Repeated ban - keep under watch.",
            author_id="moderator:lynx",
            author_name="Lynx",
            pinned=True,
        )

        self._create_sanction(
            alice,
            stype=SanctionType.mute,
            status=SanctionStatus.expired,
            reason="Spam links",
            issued_by="moderator:kate",
            issued_at=now - timedelta(days=30),
            starts_at=now - timedelta(days=30),
            ends_at=now - timedelta(days=23),
        )
        ban = self._create_sanction(
            bob,
            stype=SanctionType.ban,
            status=SanctionStatus.active,
            reason="Fraudulent activity",
            issued_by="moderator:lynx",
            issued_at=now - timedelta(days=2),
            starts_at=now - timedelta(days=2),
            ends_at=now + timedelta(days=5),
            evidence=["https://cdn.example/evidence/bob.png"],
        )

        content1 = self._create_content(
            content_id="cnt-100",
            content_type=ContentType.node,
            author_id=bob.id,
            created_at=now - timedelta(hours=5),
            preview="Guide to free gems",
            ai_labels=["spam", "scam"],
            status=ContentStatus.pending,
            meta={"queue": "nodes"},
        )
        content2 = self._create_content(
            content_id="cnt-101",
            content_type=ContentType.comment,
            author_id=alice.id,
            created_at=now - timedelta(hours=8),
            preview="I totally agree!",
            ai_labels=["positive"],
            status=ContentStatus.resolved,
            meta={"queue": "comments"},
        )

        self._create_report(
            content=content1,
            reporter_id=charlie.id,
            category="spam",
            text="Looks like a scam",
            created_at=now - timedelta(hours=4, minutes=20),
            source="user",
        )
        self._create_report(
            content=content1,
            reporter_id=alice.id,
            category="hate",
            text="Contains slurs",
            status=ReportStatus.valid,
            created_at=now - timedelta(hours=3, minutes=45),
            source="ai",
            notes="Auto classified by AI",
        )
        self._create_report(
            content=content2,
            reporter_id=bob.id,
            category="abuse",
            text="Personal attack",
            status=ReportStatus.invalid,
            created_at=now - timedelta(hours=2),
            source="user",
        )

        ticket1 = self._create_ticket(
            title="User appeal follow-up",
            author_id=bob.id,
            priority=TicketPriority.high,
            assignee_id="moderator:lynx",
            status=TicketStatus.progress,
            created_at=now - timedelta(hours=6),
        )
        self._create_ticket_message(
            ticket1,
            author_id=bob.id,
            author_name="bob",
            text="Please review my case",
            created_at=now - timedelta(hours=6),
        )
        self._create_ticket_message(
            ticket1,
            author_id="moderator:lynx",
            author_name="Lynx",
            text="We are looking into it.",
            created_at=now - timedelta(hours=5, minutes=30),
        )
        ticket1.unread_count = 0

        ticket2 = self._create_ticket(
            title="Content review request",
            author_id=charlie.id,
            priority=TicketPriority.normal,
            assignee_id="moderator:kate",
            status=TicketStatus.waiting,
            created_at=now - timedelta(days=1, hours=2),
        )
        self._create_ticket_message(
            ticket2,
            author_id=charlie.id,
            author_name="charlie",
            text="Need clarification on policy",
            created_at=now - timedelta(days=1, hours=2),
        )
        ticket2.unread_count = 1

        self._create_appeal(
            sanction=ban,
            user_id=bob.id,
            text="I was hacked",
            status="pending",
            created_at=now - timedelta(days=1),
        )

        rule1 = self._create_ai_rule(
            category="spam",
            thresholds={"spam": 0.85},
            actions={"auto_hide": True, "escalate": False},
            enabled=True,
            updated_by="admin:vera",
            description="Hide content when spam probability >= 0.85",
        )
        self._create_ai_rule(
            category="hate",
            thresholds={"hate": 0.7},
            actions={"auto_flag": True, "notify": True},
            enabled=True,
            updated_by="admin:vera",
            description="Escalate hate speech automatically",
        )

        content1.moderation_history.append(
            {
                "actor": "ai-moderator",
                "action": "flag",
                "decided_at": self._iso(now - timedelta(hours=4)),
                "reason": "High spam probability",
            }
        )
        content2.moderation_history.append(
            {
                "actor": "moderator:kate",
                "action": "keep",
                "decided_at": self._iso(now - timedelta(hours=6)),
                "reason": "No violation",
            }
        )
        rule1.history.append(
            {
                "updated_at": self._iso(now - timedelta(hours=12)),
                "updated_by": "admin:vera",
                "changes": {"description": "Initial rollout"},
            }
        )

    async def list_users(
        self,
        *,
        status: str | None = None,
        role: str | None = None,
        registered_from: str | None = None,
        registered_to: str | None = None,
        q: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            users = list(self._users.values())

        status_filters = {
            ("banned" if s in {"ban", "banned"} else s.lower())
            for s in (status.split(",") if status else [])
            if s
        }
        role_filters = {r.lower() for r in (role.split(",") if role else []) if r}
        reg_from = self._parse_datetime(registered_from)
        reg_to = self._parse_datetime(registered_to)
        q_norm = q.lower().strip() if q else None

        filtered: list[UserRecord] = []
        for user in users:
            user_statuses = {user.status.lower()}
            for sanction in self._get_sanctions_for_user(user):
                if sanction.status == SanctionStatus.active:
                    user_statuses.add(sanction.type.value.lower())
                    if sanction.type == SanctionType.ban:
                        user_statuses.add("banned")
            if status_filters and not (user_statuses & status_filters):
                continue
            if role_filters and not any(r.lower() in role_filters for r in user.roles):
                continue
            if reg_from and user.registered_at < reg_from:
                continue
            if reg_to and user.registered_at > reg_to:
                continue
            if q_norm:
                haystack = " ".join(filter(None, [user.username, user.email])).lower()
                if q_norm not in haystack:
                    continue
            filtered.append(user)

        filtered.sort(key=lambda u: u.registered_at, reverse=True)
        chunk, next_cursor = self._paginate(filtered, limit, cursor)
        return {
            "items": [self._user_to_summary(u) for u in chunk],
            "next_cursor": next_cursor,
        }

    async def get_user(self, user_id: str) -> UserDetail:
        async with self._lock:
            record = self._users.get(user_id)
            if not record:
                raise KeyError(user_id)
            return self._user_to_detail(record)

    async def update_roles(
        self, user_id: str, add: Iterable[str], remove: Iterable[str]
    ) -> list[str]:
        async with self._lock:
            record = self._users.get(user_id)
            if not record:
                raise KeyError(user_id)
            current = {r for r in record.roles}
            for role in remove:
                if role is not None:
                    current.discard(str(role))
            for role in add:
                if role is not None:
                    current.add(str(role))
            record.roles = sorted(current, key=lambda r: r.lower())
            return list(record.roles)

    async def issue_sanction(
        self,
        user_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> SanctionDTO:
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise KeyError(user_id)
            if idempotency_key and idempotency_key in self._idempotency:
                sid = self._idempotency[idempotency_key]
                sanction = self._sanctions.get(sid)
                if sanction:
                    return self._sanction_to_dto(sanction)
            try:
                stype = SanctionType(str(body.get("type", SanctionType.ban.value)))
            except ValueError as exc:
                raise ValueError("invalid_sanction_type") from exc
            status_value = body.get("status")
            status = (
                SanctionStatus(str(status_value))
                if status_value
                else SanctionStatus.active
            )
            now = self._now()
            starts_at = self._parse_datetime(body.get("starts_at")) or now
            ends_at = self._parse_datetime(
                body.get("ends_at") or body.get("expires_at")
            )
            duration_hours = body.get("duration_hours")
            if ends_at is None and duration_hours is not None:
                try:
                    ends_at = starts_at + timedelta(hours=float(duration_hours))
                except Exception:
                    pass
            if ends_at and ends_at <= now and status == SanctionStatus.active:
                status = SanctionStatus.expired
            sanction = self._create_sanction(
                user,
                stype=stype,
                status=status,
                reason=str(body.get("reason") or None),
                issued_by=body.get("issued_by") or actor_id or "system",
                issued_at=now,
                starts_at=starts_at,
                ends_at=ends_at,
                evidence=body.get("evidence"),
                meta=body.get("meta"),
            )
            if idempotency_key:
                self._idempotency[idempotency_key] = sanction.id
            # Auto-ban after 3 warnings within 10 days
            if (
                stype == SanctionType.warning
                and sanction.status == SanctionStatus.active
            ):
                recent = 0
                since = now - timedelta(days=10)
                for sid in user.sanction_ids:
                    s = self._sanctions.get(sid)
                    if not s:
                        continue
                    if (
                        s.type == SanctionType.warning
                        and s.status == SanctionStatus.active
                        and s.issued_at >= since
                    ):
                        recent += 1
                if recent >= 3:
                    self._create_sanction(
                        user,
                        stype=SanctionType.ban,
                        status=SanctionStatus.active,
                        reason=f"auto_ban_three_warnings ({recent}/3)",
                        issued_by=actor_id or "system",
                        issued_at=now,
                        starts_at=now,
                        ends_at=None,
                        evidence=None,
                        meta={
                            "source": "auto_ban",
                            "window_days": 10,
                            "warnings_count": recent,
                        },
                    )
            return self._sanction_to_dto(sanction)

    async def update_sanction(
        self,
        user_id: str,
        sanction_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> SanctionDTO:
        async with self._lock:
            sanction = self._sanctions.get(sanction_id)
            if not sanction or sanction.user_id != user_id:
                raise KeyError(sanction_id)
            if "status" in body and body["status"] is not None:
                try:
                    sanction.status = SanctionStatus(str(body["status"]))
                except ValueError as exc:
                    raise ValueError("invalid_sanction_status") from exc
            if "reason" in body:
                sanction.reason = str(body.get("reason") or None)
            if "ends_at" in body or "expires_at" in body:
                sanction.ends_at = self._parse_datetime(
                    body.get("ends_at") or body.get("expires_at")
                )
            if "evidence" in body:
                sanction.evidence = list(body.get("evidence") or [])
            metadata = body.get("meta") or body.get("metadata")
            if metadata:
                sanction.meta.update(dict(metadata))
            if body.get("revoke") or (
                body.get("status") == SanctionStatus.canceled.value
            ):
                sanction.status = SanctionStatus.canceled
                sanction.revoked_at = self._now()
                sanction.revoked_by = actor_id or body.get("revoked_by") or "system"
            if (
                sanction.ends_at
                and sanction.ends_at <= self._now()
                and sanction.status == SanctionStatus.active
            ):
                sanction.status = SanctionStatus.expired
            user = self._users.get(user_id)
            if user and sanction.type == SanctionType.ban:
                has_active_ban = any(
                    self._sanctions[sid].status == SanctionStatus.active
                    and self._sanctions[sid].type == SanctionType.ban
                    for sid in user.sanction_ids
                    if sid in self._sanctions
                )
                user.status = "banned" if has_active_ban else "active"
            return self._sanction_to_dto(sanction)

    async def add_note(
        self,
        user_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
        actor_name: str | None = None,
    ) -> ModeratorNoteDTO:
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                raise KeyError(user_id)
            note = ModeratorNoteRecord(
                id=self._generate_id("note"),
                user_id=user.id,
                text=str(body.get("text") or ""),
                created_at=self._parse_datetime(body.get("created_at")) or self._now(),
                author_id=body.get("author_id") or actor_id,
                author_name=body.get("author_name") or actor_name,
                pinned=bool(body.get("pinned") or False),
                meta=dict(body.get("meta") or {}),
            )
            self._notes[note.id] = note
            user.note_ids.insert(0, note.id)
            return self._note_to_dto(note)

    async def list_content(
        self,
        *,
        content_type: ContentType | None = None,
        status: str | None = None,
        ai_label: str | None = None,
        has_reports: bool | None = None,
        author_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            items = list(self._content.values())

        status_filter = status.lower() if status else None
        ai_label_filter = ai_label.lower() if ai_label else None
        author_filter = author_id
        created_from = self._parse_datetime(date_from)
        created_to = self._parse_datetime(date_to)

        filtered: list[ContentRecord] = []
        for content in items:
            if content_type and content.content_type != content_type:
                continue
            if status_filter and content.status.value.lower() != status_filter:
                continue
            if ai_label_filter and ai_label_filter not in [
                label.lower() for label in content.ai_labels
            ]:
                continue
            if has_reports is not None:
                present = len(content.report_ids) > 0
                if bool(has_reports) != present:
                    continue
            if author_filter and content.author_id != author_filter:
                continue
            if created_from and content.created_at < created_from:
                continue
            if created_to and content.created_at > created_to:
                continue
            filtered.append(content)

        filtered.sort(key=lambda c: c.created_at, reverse=True)
        chunk, next_cursor = self._paginate(filtered, limit, cursor)
        return {
            "items": [self._content_to_summary(c) for c in chunk],
            "next_cursor": next_cursor,
        }

    async def get_content(self, content_id: str) -> ContentSummary:
        async with self._lock:
            content = self._content.get(content_id)
            if not content:
                raise KeyError(content_id)
            return self._content_to_summary(content)

    async def decide_content(
        self,
        content_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            content = self._content.get(content_id)
            if not content:
                raise KeyError(content_id)
            action = str(body.get("action", "keep")).lower()
            reason = body.get("reason")
            now = self._now()
            decision_entry = {
                "action": action,
                "reason": reason,
                "actor": actor_id or body.get("actor") or "system",
                "decided_at": self._iso(now),
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
            return {
                "content_id": content_id,
                "status": content.status.value,
                "decision": decision_entry,
            }

    async def edit_content(
        self, content_id: str, patch: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._lock:
            content = self._content.get(content_id)
            if not content:
                raise KeyError(content_id)
            update = dict(patch or {})
            if update:
                content.meta.update(update)
            return {"content_id": content_id, "meta": dict(content.meta)}

    async def list_reports(
        self,
        *,
        category: str | None = None,
        status: ReportStatus | str | None = None,
        object_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            reports = list(self._reports.values())

        category_filter = category.lower() if category else None
        if isinstance(status, ReportStatus):
            status_filter = status.value
        else:
            status_filter = str(status).lower() if status else None
        object_filter = object_type.lower() if object_type else None
        created_from = self._parse_datetime(date_from)
        created_to = self._parse_datetime(date_to)

        filtered: list[ReportRecord] = []
        for report in reports:
            if category_filter and report.category.lower() != category_filter:
                continue
            if status_filter and report.status.value.lower() != status_filter:
                continue
            if object_filter and report.object_type.lower() != object_filter:
                continue
            created_at = report.created_at or self._now()
            if created_from and created_at < created_from:
                continue
            if created_to and created_at > created_to:
                continue
            filtered.append(report)

        filtered.sort(
            key=lambda r: r.created_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        chunk, next_cursor = self._paginate(filtered, limit, cursor)
        return {
            "items": [self._report_to_dto(r) for r in chunk],
            "next_cursor": next_cursor,
        }

    async def get_report(self, report_id: str) -> ReportDTO:
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                raise KeyError(report_id)
            return self._report_to_dto(report)

    async def resolve_report(
        self,
        report_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                raise KeyError(report_id)
            result = body.get("result")
            decision = body.get("decision")
            notes = body.get("notes")
            now = self._now()
            if result:
                norm = str(result).lower()
                if norm in {"valid", "confirmed"}:
                    report.status = ReportStatus.valid
                elif norm in {"invalid", "dismissed"}:
                    report.status = ReportStatus.invalid
                elif norm in {"escalated"}:
                    report.status = ReportStatus.escalated
                else:
                    report.status = ReportStatus.resolved
            else:
                report.status = ReportStatus.resolved
            report.decision = decision
            report.notes = notes
            report.resolved_at = now
            report.updates.append(
                {
                    "actor": actor_id or "system",
                    "result": report.status.value,
                    "decision": decision,
                    "notes": notes,
                    "resolved_at": self._iso(now),
                }
            )
            if decision == "ban" and report.object_id in self._sanctions:
                sanction = self._sanctions[report.object_id]
                sanction.meta.setdefault("related_reports", []).append(report.id)
            return {
                "report_id": report_id,
                "status": report.status.value,
                "decision": decision,
                "notes": notes,
            }

    async def list_tickets(
        self,
        *,
        status: TicketStatus | str | None = None,
        priority: TicketPriority | str | None = None,
        author: str | None = None,
        assignee: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            tickets = list(self._tickets.values())

        if isinstance(status, TicketStatus):
            status_filter = status.value
        else:
            status_filter = str(status).lower() if status else None
        if isinstance(priority, TicketPriority):
            priority_filter = priority.value
        else:
            priority_filter = str(priority).lower() if priority else None
        author_filter = author
        assignee_filter = assignee
        created_from = self._parse_datetime(date_from)
        created_to = self._parse_datetime(date_to)

        filtered: list[TicketRecord] = []
        for ticket in tickets:
            if status_filter and ticket.status.value.lower() != status_filter:
                continue
            if priority_filter and ticket.priority.value.lower() != priority_filter:
                continue
            if author_filter and ticket.author_id != author_filter:
                continue
            if assignee_filter and ticket.assignee_id != assignee_filter:
                continue
            created_at = ticket.created_at or self._now()
            if created_from and created_at < created_from:
                continue
            if created_to and created_at > created_to:
                continue
            filtered.append(ticket)

        filtered.sort(
            key=lambda t: t.updated_at
            or t.created_at
            or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        chunk, next_cursor = self._paginate(filtered, limit, cursor)
        return {
            "items": [self._ticket_to_dto(t) for t in chunk],
            "next_cursor": next_cursor,
        }

    async def get_ticket(self, ticket_id: str) -> TicketDTO:
        async with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                raise KeyError(ticket_id)
            return self._ticket_to_dto(ticket)

    async def list_ticket_messages(
        self, ticket_id: str, limit: int = 50, cursor: str | None = None
    ) -> dict[str, Any]:
        async with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                raise KeyError(ticket_id)
            messages = [
                self._ticket_messages[mid]
                for mid in ticket.message_ids
                if mid in self._ticket_messages
            ]
        messages.sort(key=lambda m: m.created_at or datetime.min.replace(tzinfo=UTC))
        chunk, next_cursor = self._paginate(messages, limit, cursor)
        return {
            "items": [self._ticket_message_to_dto(m) for m in chunk],
            "next_cursor": next_cursor,
        }

    async def add_ticket_message(
        self,
        ticket_id: str,
        body: dict[str, Any],
        *,
        author_id: str,
        author_name: str | None = None,
    ) -> TicketMessageDTO:
        async with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                raise KeyError(ticket_id)
            message = TicketMessageRecord(
                id=self._generate_id("msg"),
                ticket_id=ticket.id,
                author_id=author_id,
                text=str(body.get("text") or ""),
                attachments=[dict(a) for a in body.get("attachments") or []],
                internal=bool(body.get("internal") or False),
                author_name=author_name or body.get("author_name"),
                created_at=self._parse_datetime(body.get("created_at")) or self._now(),
            )
            self._ticket_messages[message.id] = message
            ticket.message_ids.append(message.id)
            ticket.last_message_at = message.created_at
            ticket.updated_at = message.created_at
            if body.get("increment_unread", True) and not message.internal:
                ticket.unread_count = max(ticket.unread_count, 0) + 1
            return self._ticket_message_to_dto(message)

    async def update_ticket(
        self, ticket_id: str, patch: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                raise KeyError(ticket_id)
            if "status" in patch and patch["status"] is not None:
                try:
                    ticket.status = TicketStatus(str(patch["status"]))
                except ValueError as exc:
                    raise ValueError("invalid_ticket_status") from exc
            if "priority" in patch and patch["priority"] is not None:
                try:
                    ticket.priority = TicketPriority(str(patch["priority"]))
                except ValueError as exc:
                    raise ValueError("invalid_ticket_priority") from exc
            if "assignee_id" in patch:
                ticket.assignee_id = patch["assignee_id"]
            if "unread_count" in patch:
                try:
                    ticket.unread_count = max(0, int(patch["unread_count"]))
                except Exception:
                    ticket.unread_count = max(ticket.unread_count, 0)
            if "meta" in patch and patch["meta"]:
                ticket.meta.update(dict(patch["meta"]))
            ticket.updated_at = self._now()
            return {
                "ticket_id": ticket_id,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "assignee_id": ticket.assignee_id,
            }

    async def escalate_ticket(
        self,
        ticket_id: str,
        payload: dict[str, Any] | None = None,
        *,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                raise KeyError(ticket_id)
            ticket.status = TicketStatus.escalated
            ticket.meta.setdefault("escalations", []).append(
                {
                    "actor": actor_id or "system",
                    "reason": (payload or {}).get("reason"),
                    "at": self._iso(self._now()),
                }
            )
            ticket.updated_at = self._now()
            return {
                "ticket_id": ticket_id,
                "status": ticket.status.value,
                "escalated": True,
            }

    async def list_appeals(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        target_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            appeals = list(self._appeals.values())

        status_filter = status.lower() if status else None
        user_filter = user_id
        target_filter = target_type.lower() if target_type else None
        created_from = self._parse_datetime(date_from)
        created_to = self._parse_datetime(date_to)

        filtered: list[AppealRecord] = []
        for appeal in appeals:
            if status_filter and appeal.status.lower() != status_filter:
                continue
            if user_filter and appeal.user_id != user_filter:
                continue
            if target_filter and appeal.target_type.lower() != target_filter:
                continue
            created_at = appeal.created_at or self._now()
            if created_from and created_at < created_from:
                continue
            if created_to and created_at > created_to:
                continue
            filtered.append(appeal)

        filtered.sort(
            key=lambda a: a.created_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        chunk, next_cursor = self._paginate(filtered, limit, cursor)
        return {
            "items": [self._appeal_to_dto(a) for a in chunk],
            "next_cursor": next_cursor,
        }

    async def get_appeal(self, appeal_id: str) -> AppealDTO:
        async with self._lock:
            appeal = self._appeals.get(appeal_id)
            if not appeal:
                raise KeyError(appeal_id)
            return self._appeal_to_dto(appeal)

    async def decide_appeal(
        self,
        appeal_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._lock:
            appeal = self._appeals.get(appeal_id)
            if not appeal:
                raise KeyError(appeal_id)
            result = str(body.get("result", "approved")).lower()
            appeal.status = result
            appeal.decision_reason = body.get("reason")
            appeal.decided_by = actor_id or body.get("decided_by") or "system"
            appeal.decided_at = self._now()
            appeal.meta.setdefault("history", []).append(
                {
                    "actor": appeal.decided_by,
                    "result": result,
                    "reason": appeal.decision_reason,
                    "decided_at": self._iso(appeal.decided_at),
                }
            )
            if result == "approved":
                sanction = self._sanctions.get(appeal.target_id)
                if sanction:
                    sanction.status = SanctionStatus.canceled
                    sanction.revoked_at = appeal.decided_at
                    sanction.revoked_by = appeal.decided_by
            return {
                "appeal_id": appeal_id,
                "status": appeal.status,
                "decided_at": self._iso(appeal.decided_at),
            }

    async def list_rules(
        self, limit: int = 50, cursor: str | None = None
    ) -> dict[str, Any]:
        async with self._lock:
            rules = list(self._ai_rules.values())
        rules.sort(
            key=lambda r: r.updated_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        chunk, next_cursor = self._paginate(rules, limit, cursor)
        return {
            "items": [self._ai_rule_to_dto(r) for r in chunk],
            "next_cursor": next_cursor,
        }

    async def create_rule(
        self,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> AIRuleDTO:
        async with self._lock:
            rule = AIRuleRecord(
                id=self._generate_id("air"),
                category=str(body.get("category") or "generic"),
                thresholds=dict(body.get("thresholds") or {}),
                actions=dict(body.get("actions") or {}),
                enabled=bool(body.get("enabled", True)),
                updated_by=actor_id or body.get("updated_by") or "system",
                updated_at=self._now(),
                description=body.get("description"),
                history=[],
            )
            rule.history.append(
                {
                    "updated_at": self._iso(rule.updated_at),
                    "updated_by": rule.updated_by,
                    "changes": {"created": True},
                }
            )
            self._ai_rules[rule.id] = rule
            return self._ai_rule_to_dto(rule)

    async def get_rule(self, rule_id: str) -> AIRuleDTO:
        async with self._lock:
            rule = self._ai_rules.get(rule_id)
            if not rule:
                raise KeyError(rule_id)
            return self._ai_rule_to_dto(rule)

    async def update_rule(
        self,
        rule_id: str,
        body: dict[str, Any],
        *,
        actor_id: str | None = None,
    ) -> AIRuleDTO:
        async with self._lock:
            rule = self._ai_rules.get(rule_id)
            if not rule:
                raise KeyError(rule_id)
            changes: dict[str, Any] = {}
            if "category" in body and body["category"]:
                rule.category = str(body["category"])
                changes["category"] = rule.category
            if "thresholds" in body and body["thresholds"] is not None:
                rule.thresholds = dict(body["thresholds"])
                changes["thresholds"] = rule.thresholds
            if "actions" in body and body["actions"] is not None:
                rule.actions = dict(body["actions"])
                changes["actions"] = rule.actions
            if "enabled" in body:
                rule.enabled = bool(body["enabled"])
                changes["enabled"] = rule.enabled
            if "description" in body:
                rule.description = body.get("description")
                changes["description"] = rule.description
            rule.updated_by = actor_id or body.get("updated_by") or "system"
            rule.updated_at = self._now()
            if changes:
                rule.history.append(
                    {
                        "updated_at": self._iso(rule.updated_at),
                        "updated_by": rule.updated_by,
                        "changes": changes,
                    }
                )
            return self._ai_rule_to_dto(rule)

    async def delete_rule(self, rule_id: str) -> bool:
        async with self._lock:
            removed = self._ai_rules.pop(rule_id, None)
            return bool(removed)

    async def test_rule(self, payload: dict[str, Any]) -> dict[str, Any]:
        rule_id = payload.get("rule_id")
        async with self._lock:
            rule = None
            if rule_id:
                rule = self._ai_rules.get(str(rule_id))
            if not rule and self._ai_rules:
                rule = next(iter(self._ai_rules.values()))
        if not rule:
            return {"input": payload, "labels": [], "scores": {}, "decision": None}
        scores = payload.get("scores") or payload.get("probabilities") or {}
        labels = []
        decision = "pass"
        for label, threshold in rule.thresholds.items():
            try:
                value = float(scores.get(label, 0.0))
            except Exception:
                value = 0.0
            if value >= float(threshold):
                labels.append(label)
        if labels:
            decision = "flag"
        return {
            "input": payload,
            "labels": labels,
            "scores": scores,
            "decision": decision,
            "rule": self._ai_rule_to_dto(rule),
        }

    async def rules_history(
        self, limit: int = 50, cursor: str | None = None
    ) -> dict[str, Any]:
        async with self._lock:
            history_entries: list[dict[str, Any]] = []
            for rule in self._ai_rules.values():
                for entry in rule.history:
                    history_entries.append(
                        {**entry, "rule_id": rule.id, "category": rule.category}
                    )
        history_entries.sort(key=lambda e: e.get("updated_at") or "", reverse=True)
        chunk, next_cursor = self._paginate(history_entries, limit, cursor)
        return {"items": chunk, "next_cursor": next_cursor}

    async def get_overview(self, limit: int = 10) -> OverviewDTO:
        async with self._lock:
            reports = list(self._reports.values())
            tickets = list(self._tickets.values())
            sanctions = sorted(
                self._sanctions.values(), key=lambda s: s.issued_at, reverse=True
            )
            content_items = list(self._content.values())
            appeals = list(self._appeals.values())

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

        last_sanctions = [self._sanction_to_dto(s) for s in sanctions[:limit]]

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
        ai_share = (
            float(ai_decisions) / float(total_decisions) if total_decisions else 0.0
        )

        cards: list[CardDTO] = []
        flagged_users = [
            self._user_to_summary(self._users[s.user_id])
            for s in sanctions
            if s.status == SanctionStatus.active and s.user_id in self._users
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
