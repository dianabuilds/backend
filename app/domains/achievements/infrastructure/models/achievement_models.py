from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.core.db.adapters import UUID
from app.schemas.content_common import ContentStatus, ContentVisibility


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    condition = Column(JSON, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)
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

    users = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(UUID(), ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    achievement = relationship("Achievement", back_populates="users")
