from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, String, Integer

from app.core.db.base import Base
from app.core.db.adapters import UUID
from app.schemas.content_common import ContentStatus, ContentVisibility


class NotificationType(str, Enum):
    quest = "quest"
    system = "system"
    moderation = "moderation"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    type = Column(SAEnum(NotificationType), nullable=False, default=NotificationType.system)
    status = Column(
        SAEnum(ContentStatus, name="content_status"),
        nullable=False,
        server_default=ContentStatus.draft.value,
    )
    version = Column(Integer, nullable=False, server_default="1")
    visibility = Column(
        SAEnum(ContentVisibility, name="content_visibility"),
        nullable=False,
        server_default=ContentVisibility.private.value,
    )
    created_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
