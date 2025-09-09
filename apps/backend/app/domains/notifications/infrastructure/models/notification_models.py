from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum

from app.providers.db.adapters import UUID
from app.providers.db.base import Base
from app.schemas.nodes_common import Status, Visibility
from app.schemas.notification import NotificationPlacement, NotificationType


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(), primary_key=True, default=uuid4)
    profile_id = Column(UUID(), nullable=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    type = Column(SAEnum(NotificationType), nullable=False, default=NotificationType.system)
    placement = Column(
        SAEnum(NotificationPlacement),
        nullable=False,
        default=NotificationPlacement.inbox,
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
    is_preview = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
