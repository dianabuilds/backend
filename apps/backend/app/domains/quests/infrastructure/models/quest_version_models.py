from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.kernel.db import JSONB, UUID, Base


class QuestVersion(Base):
    __tablename__ = "quest_versions"
    __table_args__ = (UniqueConstraint("quest_id", "number", name="uq_quest_version_number"),)

    id = Column(UUID(), primary_key=True, default=uuid4)
    quest_id = Column(UUID(), ForeignKey("quests.id"), nullable=False, index=True)
    number = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(), nullable=True)
    released_at = Column(DateTime, nullable=True)
    released_by = Column(UUID(), nullable=True)
    parent_version_id = Column(UUID(), nullable=True)
    meta = Column(JSONB, nullable=True)

    nodes = relationship("QuestGraphNode", cascade="all, delete-orphan", back_populates="version")
    edges = relationship("QuestGraphEdge", cascade="all, delete-orphan", back_populates="version")


class QuestGraphNode(Base):
    __tablename__ = "quest_graph_nodes"
    __table_args__ = (UniqueConstraint("version_id", "key", name="uq_qnode_key"),)

    id = Column(UUID(), primary_key=True, default=uuid4)
    version_id = Column(
        UUID(),
        ForeignKey("quest_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key = Column(String, nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False, default="normal")
    content = Column(JSONB, nullable=True)
    rewards = Column(JSONB, nullable=True)

    version = relationship("QuestVersion", back_populates="nodes")


class QuestGraphEdge(Base):
    __tablename__ = "quest_graph_edges"

    id = Column(UUID(), primary_key=True, default=uuid4)
    version_id = Column(
        UUID(),
        ForeignKey("quest_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_node_key = Column(String, nullable=False)
    to_node_key = Column(String, nullable=False)
    label = Column(String, nullable=True)
    condition = Column(JSONB, nullable=True)

    version = relationship("QuestVersion", back_populates="edges")


class DraftLock(Base):
    __tablename__ = "quest_draft_locks"

    id = Column(UUID(), primary_key=True, default=uuid4)
    version_id = Column(
        UUID(),
        ForeignKey("quest_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

