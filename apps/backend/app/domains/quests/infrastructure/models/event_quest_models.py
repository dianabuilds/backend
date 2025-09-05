from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.ext.mutable import MutableList

from app.models.adapters import ARRAY, UUID  # типы-адаптеры остаются в core
from app.providers.db.base import Base


class EventQuestRewardType(str, Enum):
    achievement = "achievement"
    premium = "premium"
    custom = "custom"


class EventQuest(Base):
    __tablename__ = "event_quests"

    id = Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    target_node_id = Column(BigInteger, ForeignKey("nodes.id"), nullable=False)
    hints_tags = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    hints_keywords = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    hints_trace = Column(MutableList.as_mutable(ARRAY(UUID())), default=list)
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    max_rewards = Column(Integer, default=0)
    reward_type = Column(SAEnum(EventQuestRewardType), nullable=False)
    is_active = Column(Boolean, default=False)


class EventQuestCompletion(Base):
    __tablename__ = "event_quest_completions"
    __table_args__ = (UniqueConstraint("quest_id", "user_id", name="uq_event_quest_user"),)

    id = Column(UUID(), primary_key=True, default=uuid4)
    quest_id = Column(UUID(), ForeignKey("event_quests.id"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    node_id = Column(BigInteger, ForeignKey("nodes.id"), nullable=False)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    completed_at = Column(DateTime, default=datetime.utcnow)
