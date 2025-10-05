from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .dtos import (
    ContentStatus,
    ContentType,
    ReportStatus,
    SanctionStatus,
    SanctionType,
    TicketPriority,
    TicketStatus,
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
    def type(self) -> ContentType:
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


__all__ = [
    "AIRuleRecord",
    "AppealRecord",
    "ContentRecord",
    "ModeratorNoteRecord",
    "ReportRecord",
    "SanctionRecord",
    "TicketMessageRecord",
    "TicketRecord",
    "UserRecord",
]
