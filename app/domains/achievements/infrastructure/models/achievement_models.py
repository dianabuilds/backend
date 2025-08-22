from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.core.db.adapters import UUID


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(UUID(), primary_key=True, default=uuid4)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    condition = Column(JSON, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)

    users = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(UUID(), ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    achievement = relationship("Achievement", back_populates="users")
