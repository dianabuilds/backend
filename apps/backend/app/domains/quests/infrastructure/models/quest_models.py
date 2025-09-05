from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

from app.providers.db.adapters import ARRAY, JSONB, UUID
from app.providers.db.base import Base
from app.schemas.nodes_common import Status, Visibility


def generate_slug() -> str:
    seed = f"{datetime.utcnow().isoformat()}-{uuid4()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


class Quest(Base):
    __tablename__ = "quests"

    id = Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = Column(
        UUID(), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    slug = Column(
        String, unique=True, index=True, nullable=False, default=generate_slug
    )
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    tags = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    author_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    price = Column(Integer, nullable=True)
    is_premium_only = Column(Boolean, default=False)
    entry_node_id = Column(BigInteger, ForeignKey("nodes.id"), nullable=True)
    nodes = Column(MutableList.as_mutable(ARRAY(BigInteger)), default=list)
    custom_transitions = Column(MutableDict.as_mutable(JSONB), nullable=True)
    structure = Column(String, nullable=True)
    length = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    locale = Column(String, nullable=True)
    cost_generation = Column(Integer, nullable=True)
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
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    allow_comments = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    purchases = relationship(
        "QuestPurchase", back_populates="quest", cascade="all, delete-orphan"
    )
    progresses = relationship(
        "QuestProgress", back_populates="quest", cascade="all, delete-orphan"
    )


class QuestPurchase(Base):
    __tablename__ = "quest_purchases"

    id = Column(UUID(), primary_key=True, default=uuid4)
    quest_id = Column(UUID(), ForeignKey("quests.id"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    workspace_id = Column(
        UUID(), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    paid_at = Column(DateTime, default=datetime.utcnow)

    quest = relationship("Quest", back_populates="purchases")


class QuestProgress(Base):
    __tablename__ = "quest_progress"
    __table_args__ = (
        UniqueConstraint("quest_id", "user_id", name="uq_quest_progress"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    quest_id = Column(UUID(), ForeignKey("quests.id"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    workspace_id = Column(
        UUID(), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    current_node_id = Column(BigInteger, ForeignKey("nodes.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    quest = relationship("Quest", back_populates="progresses")
