from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, String

from . import Base
from .adapters import UUID


class NotificationType(str, Enum):
    quest = "quest"
    system = "system"
    moderation = "moderation"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    type = Column(SAEnum(NotificationType), nullable=False, default=NotificationType.system)
