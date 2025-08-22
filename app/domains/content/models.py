from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.core.db.adapters import UUID
from app.schemas.content_common import ContentStatus


class ContentItem(Base):
    __tablename__ = "content_items"

    id = sa.Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = sa.Column(UUID(), sa.ForeignKey("workspaces.id"), nullable=False)
    type = sa.Column(sa.String, nullable=False)
    status = sa.Column(
        sa.Enum(ContentStatus, name="content_status"),
        nullable=False,
        server_default=ContentStatus.draft.value,
    )
    version = sa.Column(sa.Integer, nullable=False, server_default="1")
    slug = sa.Column(sa.String, unique=True, index=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    summary = sa.Column(sa.Text, nullable=True)
    cover_media_id = sa.Column(UUID(), nullable=True)
    primary_tag_id = sa.Column(UUID(), sa.ForeignKey("tags.id"), nullable=True)
    created_by_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=True)
    updated_by_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=True)
    published_at = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = relationship("Tag", secondary="content_tags", back_populates="content_items")
