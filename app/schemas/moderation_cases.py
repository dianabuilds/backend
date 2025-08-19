from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CaseListItem(BaseModel):
    id: UUID
    type: str
    status: str
    priority: str
    summary: str
    target_type: str | None = None
    target_id: str | None = None
    assignee_id: UUID | None = None
    labels: list[str] = Field(default_factory=list)
    created_at: datetime
    due_at: datetime | None = None
    last_event_at: datetime | None = None

    model_config = {"from_attributes": True}


class CaseCreateIn(BaseModel):
    type: str
    summary: str
    details: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    reporter_id: UUID | None = None
    reporter_contact: str | None = None
    priority: str | None = None
    labels: list[str] | None = None
    assignee_id: UUID | None = None


class CasePatchIn(BaseModel):
    summary: str | None = None
    details: str | None = None
    priority: str | None = None
    status: str | None = None
    assignee_id: UUID | None = None
    due_at: datetime | None = None


class CaseNoteOut(BaseModel):
    id: UUID
    author_id: UUID | None = None
    created_at: datetime
    text: str
    internal: bool

    model_config = {"from_attributes": True}


class CaseNoteCreateIn(BaseModel):
    text: str
    internal: bool | None = True


class CaseAttachmentOut(BaseModel):
    id: UUID
    author_id: UUID | None = None
    created_at: datetime
    url: str
    title: str | None = None
    media_type: str | None = None

    model_config = {"from_attributes": True}


class CaseAttachmentCreateIn(BaseModel):
    url: str
    title: str | None = None
    media_type: str | None = None


class CaseEventOut(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    created_at: datetime
    kind: str
    payload: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class CaseFull(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    type: str
    status: str
    priority: str
    reporter_id: UUID | None = None
    reporter_contact: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    summary: str
    details: str | None = None
    assignee_id: UUID | None = None
    due_at: datetime | None = None
    first_response_due_at: datetime | None = None
    last_event_at: datetime | None = None
    source: str | None = None
    reason_code: str | None = None
    resolution: str | None = None
    labels: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    page: int
    size: int
    total: int


class CloseCaseIn(BaseModel):
    resolution: str  # resolved | rejected
    reason_code: str | None = None
    reason_text: str | None = None


class EscalateIn(BaseModel):
    to_role: str | None = None
    reason_text: str | None = None


class LabelsPatchIn(BaseModel):
    add: list[str] | None = None
    remove: list[str] | None = None
