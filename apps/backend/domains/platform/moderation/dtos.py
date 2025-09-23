from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    node = "node"
    comment = "comment"
    trail = "trail"
    media = "media"


class ContentStatus(str, Enum):
    pending = "pending"
    resolved = "resolved"
    hidden = "hidden"
    restricted = "restricted"
    escalated = "escalated"


class SanctionType(str, Enum):
    ban = "ban"
    mute = "mute"
    limit = "limit"
    shadowban = "shadowban"
    warning = "warning"


class SanctionStatus(str, Enum):
    active = "active"
    expired = "expired"
    canceled = "canceled"


class ReportStatus(str, Enum):
    new = "new"
    valid = "valid"
    invalid = "invalid"
    resolved = "resolved"
    escalated = "escalated"


class TicketStatus(str, Enum):
    new = "new"
    progress = "progress"
    waiting = "waiting"
    solved = "solved"
    closed = "closed"
    escalated = "escalated"


class TicketPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class CardAction(BaseModel):
    key: str
    label: str
    kind: Literal["primary", "secondary", "danger", "ghost"] = "primary"


class CardDTO(BaseModel):
    type: str
    id: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    avatar: str | None = None
    preview: str | None = None
    tags: list[str] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    status: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    actions: list[CardAction] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)
    roleVisibility: list[str] = Field(default_factory=list)


class ModeratorNoteDTO(BaseModel):
    id: str
    text: str
    author_id: str | None = None
    author_name: str | None = None
    created_at: str | None = None
    pinned: bool = False
    meta: dict[str, Any] = Field(default_factory=dict)


class ReportDTO(BaseModel):
    id: str
    object_type: str
    object_id: str
    reporter_id: str
    category: str
    text: str | None = None
    status: ReportStatus = ReportStatus.new
    created_at: str | None = None
    resolved_at: str | None = None
    decision: str | None = None
    notes: str | None = None
    updates: list[dict[str, Any]] = Field(default_factory=list)
    source: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class SanctionDTO(BaseModel):
    id: str
    type: SanctionType
    status: SanctionStatus
    reason: str | None = None
    issued_by: str | None = None
    issued_at: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    revoked_at: str | None = None
    revoked_by: str | None = None
    evidence: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class TicketMessageDTO(BaseModel):
    id: str
    ticket_id: str
    author_id: str
    text: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    internal: bool = False
    author_name: str | None = None
    created_at: str | None = None


class TicketDTO(BaseModel):
    id: str
    title: str
    priority: TicketPriority = TicketPriority.normal
    author_id: str
    assignee_id: str | None = None
    status: TicketStatus = TicketStatus.new
    created_at: str | None = None
    updated_at: str | None = None
    last_message_at: str | None = None
    unread_count: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)


class AppealDTO(BaseModel):
    id: str
    target_type: str
    target_id: str
    user_id: str
    text: str | None = None
    status: str = "new"
    created_at: str | None = None
    decided_at: str | None = None
    decided_by: str | None = None
    decision_reason: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class AIRuleDTO(BaseModel):
    id: str
    category: str
    thresholds: dict[str, Any] = Field(default_factory=dict)
    actions: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    updated_by: str | None = None
    updated_at: str | None = None
    description: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)


class ContentSummary(BaseModel):
    id: str
    type: ContentType
    author_id: str
    created_at: str | None = None
    preview: str | None = None
    ai_labels: list[str] = Field(default_factory=list)
    complaints_count: int = 0
    status: ContentStatus = ContentStatus.pending
    moderation_history: list[dict[str, Any]] = Field(default_factory=list)
    reports: list[ReportDTO] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class UserSummary(BaseModel):
    id: str
    username: str
    email: str | None = None
    roles: list[str] = Field(default_factory=list)
    status: str = "active"
    registered_at: str | None = None
    last_seen_at: str | None = None
    complaints_count: int = 0
    notes_count: int = 0
    sanction_count: int = 0
    active_sanctions: list[SanctionDTO] = Field(default_factory=list)
    last_sanction: SanctionDTO | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class UserDetail(UserSummary):
    sanctions: list[SanctionDTO] = Field(default_factory=list)
    reports: list[ReportDTO] = Field(default_factory=list)
    tickets: list[TicketDTO] = Field(default_factory=list)
    notes: list[ModeratorNoteDTO] = Field(default_factory=list)


class OverviewDTO(BaseModel):
    complaints_new: dict[str, Any] = Field(default_factory=dict)
    tickets: dict[str, Any] = Field(default_factory=dict)
    content_queues: dict[str, int] = Field(default_factory=dict)
    last_sanctions: list[SanctionDTO] = Field(default_factory=list)
    charts: dict[str, Any] = Field(default_factory=dict)
    cards: list[CardDTO] = Field(default_factory=list)


__all__ = [
    "ContentType",
    "ContentStatus",
    "SanctionType",
    "SanctionStatus",
    "ReportStatus",
    "TicketStatus",
    "TicketPriority",
    "CardDTO",
    "CardAction",
    "ModeratorNoteDTO",
    "ReportDTO",
    "SanctionDTO",
    "TicketDTO",
    "TicketMessageDTO",
    "AppealDTO",
    "AIRuleDTO",
    "ContentSummary",
    "UserSummary",
    "UserDetail",
    "OverviewDTO",
]
