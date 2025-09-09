from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class Tag(Base):
    """Simple tag used to categorize content and nodes."""

    __tablename__ = "tags"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    slug = sa.Column(sa.String, nullable=False, index=True)
    name = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    is_hidden = sa.Column(sa.Boolean, default=False, nullable=False, index=True)

    __table_args__ = (sa.UniqueConstraint("slug", name="uq_tags_slug"),)

    content_items = relationship("NodeItem", secondary="content_tags", back_populates="tags")
    nodes = relationship("Node", secondary="node_tags", back_populates="tags")


class ContentTag(Base):
    """Association table between content items and tags."""

    __tablename__ = "content_tags"

    # В базе колонка называется content_id_bigint; маппим на python‑атрибут content_id
    content_id = sa.Column(
        "content_id_bigint",
        sa.BigInteger,
        sa.ForeignKey("content_items.id_bigint", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = sa.Column(UUID(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)

    tag = relationship("Tag", overlaps="content_items")
