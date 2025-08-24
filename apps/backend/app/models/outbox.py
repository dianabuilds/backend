import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Integer, Enum as SAEnum, ForeignKey, Boolean

from .adapters import UUID as GUID, JSONB
from . import Base


class OutboxStatus(str, enum.Enum):
    NEW = "NEW"
    SENT = "SENT"
    FAILED = "FAILED"


class OutboxEvent(Base):
    """Event stored for reliable delivery via the outbox pattern."""

    __tablename__ = "outbox"

    id = Column(GUID(), primary_key=True, default=uuid4)
    topic = Column(String, nullable=False)
    payload_json = Column(JSONB(), nullable=False)
    dedup_key = Column(String, nullable=True)
    status = Column(SAEnum(OutboxStatus, name="outboxstatus"), default=OutboxStatus.NEW, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    workspace_id = Column(GUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    is_preview = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
