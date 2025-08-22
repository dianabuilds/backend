from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.core.db.adapters import JSONB, UUID, ARRAY


class NodeTransitionType(str, Enum):
    manual = "manual"
    locked = "locked"


class NodeTransition(Base):
    __tablename__ = "node_transitions"

    id = Column(UUID(), primary_key=True, default=uuid4)
    from_node_id = Column(UUID(), ForeignKey("nodes.id"), nullable=False, index=True)
    to_node_id = Column(UUID(), ForeignKey("nodes.id"), nullable=False)
    type = Column(SAEnum(NodeTransitionType), nullable=False, default=NodeTransitionType.manual)
    condition = Column(MutableDict.as_mutable(JSONB), default=dict)
    weight = Column(Integer, default=1)
    label = Column(String, nullable=True)
    created_by = Column(UUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_node = relationship("Node", foreign_keys=[from_node_id], backref="outgoing_transitions")
    to_node = relationship("Node", foreign_keys=[to_node_id])


class NodeTraceKind(str, Enum):
    auto = "auto"
    manual = "manual"
    quest_hint = "quest_hint"


class NodeTraceVisibility(str, Enum):
    public = "public"
    private = "private"
    system = "system"


class NodeTrace(Base):
    __tablename__ = "node_traces"

    id = Column(UUID(), primary_key=True, default=uuid4)
    node_id = Column(UUID(), ForeignKey("nodes.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    kind = Column(SAEnum(NodeTraceKind), nullable=False)
    comment = Column(Text, nullable=True)
    tags = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    visibility = Column(SAEnum(NodeTraceVisibility), nullable=False, default=NodeTraceVisibility.public)

    node = relationship("Node")
    user = relationship("User")
