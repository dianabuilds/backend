from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import relationship, deferred

from app.core.db.base import Base
from app.core.db.adapters import UUID


class Tag(Base):
    """Simple tag used to categorize content and nodes."""

    __tablename__ = "tags"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    # ``workspace_id`` existed in some database schemas.  Older installations
    # lack this column which previously caused ``SELECT`` statements to fail.
    # Marking it as nullable and deferred prevents SQLAlchemy from including it
    # in queries when the column is absent.
    workspace_id = sa.Column(UUID(), sa.ForeignKey("workspaces.id"), nullable=True)
    workspace_id = deferred(workspace_id)
    slug = sa.Column(sa.String, nullable=False, unique=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    is_hidden = sa.Column(sa.Boolean, default=False, nullable=False, index=True)

    content_items = relationship(
        "ContentItem", secondary="content_tags", back_populates="tags"
    )
    nodes = relationship("Node", secondary="node_tags", back_populates="tags")


class ContentTag(Base):
    """Association table between content items and tags."""

    __tablename__ = "content_tags"

    content_id = sa.Column(
        UUID(), sa.ForeignKey("content_items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = sa.Column(
        UUID(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)

    tag = relationship("Tag")

