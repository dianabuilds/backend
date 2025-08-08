from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from . import Base
from .adapters import ARRAY, UUID


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
