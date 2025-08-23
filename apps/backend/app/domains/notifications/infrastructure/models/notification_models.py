from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String

from app.core.db.adapters import UUID
from app.core.db.base import Base
from app.schemas.nodes_common import Status, Visibility


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
    type = Column(
        SAEnum(NotificationType), nullable=False, default=NotificationType.system
    )
    status = Column(
        SAEnum(Status, name="content_status"),
        nullable=False,
        server_default=Status.draft.value,
    )
    version = Column(Integer, nullable=False, server_default="1")
    visibility = Column(
        SAEnum(Visibility, name="content_visibility"),
        nullable=False,
        server_default=Visibility.private.value,
    )
    created_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
