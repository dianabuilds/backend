from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.adapters import JSONB, UUID  # используем core-адаптеры типов
from app.providers.db.base import Base


class ModerationCase(Base):
    __tablename__ = "moderation_cases"

    id = Column(UUID(), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    type = Column(
        String, nullable=False
    )  # complaint_content | complaint_user | support_request | appeal
    status = Column(
        String, nullable=False, default="new"
    )  # new | assigned | in_progress | waiting_user | resolved | rejected | escalated
    priority = Column(String, nullable=False, default="P2")  # P0 | P1 | P2

    reporter_id = Column(UUID(), nullable=True)
    reporter_contact = Column(String, nullable=True)

    target_type = Column(String, nullable=True)  # user | content | quest | tag | other
    target_id = Column(String, nullable=True)

    summary = Column(String, nullable=False)
    details = Column(Text, nullable=True)

    assignee_id = Column(UUID(), nullable=True)

    due_at = Column(DateTime, nullable=True)
    first_response_due_at = Column(DateTime, nullable=True)
    last_event_at = Column(DateTime, nullable=True)

    source = Column(String, nullable=True)  # web | api | auto

    reason_code = Column(String, nullable=True)  # при закрытии
    resolution = Column(String, nullable=True)  # resolved | rejected

    labels = relationship(
        "CaseLabel", cascade="all, delete-orphan", back_populates="case"
    )
    notes = relationship(
        "CaseNote", cascade="all, delete-orphan", back_populates="case"
    )
    attachments = relationship(
        "CaseAttachment", cascade="all, delete-orphan", back_populates="case"
    )
    events = relationship(
        "CaseEvent", cascade="all, delete-orphan", back_populates="case"
    )


class ModerationLabel(Base):
    __tablename__ = "moderation_labels"

    id = Column(UUID(), primary_key=True, default=uuid4)
    name = Column(String, unique=True, nullable=False)
    color = Column(String, nullable=True)  # hex
    protected = Column(Boolean, nullable=False, default=False)


class CaseLabel(Base):
    __tablename__ = "case_labels"

    id = Column(UUID(), primary_key=True, default=uuid4)
    case_id = Column(
        UUID(), ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False
    )
    label_id = Column(
        UUID(), ForeignKey("moderation_labels.id", ondelete="CASCADE"), nullable=False
    )

    case = relationship("ModerationCase", back_populates="labels")
    label = relationship("ModerationLabel")


class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(UUID(), primary_key=True, default=uuid4)
    case_id = Column(
        UUID(), ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(UUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    text = Column(Text, nullable=False)
    internal = Column(Boolean, default=True, nullable=False)

    case = relationship("ModerationCase", back_populates="notes")


class CaseAttachment(Base):
    __tablename__ = "case_attachments"

    id = Column(UUID(), primary_key=True, default=uuid4)
    case_id = Column(
        UUID(), ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(UUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    media_type = Column(String, nullable=True)

    case = relationship("ModerationCase", back_populates="attachments")


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(UUID(), primary_key=True, default=uuid4)
    case_id = Column(
        UUID(), ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False
    )
    actor_id = Column(UUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    kind = Column(
        String, nullable=False
    )  # assign | change_priority | add_label | remove_label | add_note |
    # add_attachment | status_change | decision_* | escalate_overdue | reopen
    payload = Column(JSONB, nullable=True)
    case = relationship("ModerationCase", back_populates="events")
