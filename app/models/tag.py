from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from .adapters import UUID
from . import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(), primary_key=True, default=uuid4)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_hidden = Column(Boolean, default=False, index=True)

    nodes = relationship("Node", secondary="node_tags", back_populates="tags")


class NodeTag(Base):
    __tablename__ = "node_tags"

    node_id = Column(UUID(), ForeignKey("nodes.id"), primary_key=True)
    tag_id = Column(UUID(), ForeignKey("tags.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
