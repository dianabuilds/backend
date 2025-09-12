from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.kernel.db import UUID, Base
from app.schemas.nodes_common import Status, Visibility


class NodeItem(Base):
    __tablename__ = "content_items"

    id = sa.Column("id_bigint", sa.BigInteger, primary_key=True)
    node_id = sa.Column(sa.BigInteger, sa.ForeignKey("nodes.id"), nullable=True, index=True)
    type = sa.Column(sa.String, nullable=False)
    status = sa.Column(
        sa.Enum(Status, name="content_status"),
        nullable=False,
        server_default=Status.draft.value,
    )
    visibility = sa.Column(
        sa.Enum(Visibility, name="content_visibility"),
        nullable=False,
        server_default=Visibility.private.value,
    )
    version = sa.Column(sa.Integer, nullable=False, server_default="1")
    slug = sa.Column(sa.String, index=True, nullable=False)
    title = sa.Column(sa.String, nullable=False)
    summary = sa.Column(sa.Text, nullable=True)
    cover_media_id = sa.Column(UUID(), nullable=True)
    primary_tag_id = sa.Column(UUID(), sa.ForeignKey("tags.id"), nullable=True)
    created_by_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=True)
    updated_by_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=True)
    published_at = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = relationship(
        "Tag",
        secondary="content_tags",
        back_populates="content_items",
        overlaps="tag",
        lazy="noload",
    )

    __table_args__ = (
        sa.Index("ix_content_items_slug", "slug"),
        sa.Index("ix_content_items_created_at", "created_at"),
    )


class NodePatch(Base):
    __tablename__ = "node_patches"

    id = sa.Column("id_bigint", sa.BigInteger, primary_key=True)
    node_id = sa.Column(
        "node_id_bigint",
        sa.BigInteger,
        sa.ForeignKey("content_items.id_bigint", ondelete="CASCADE"),
        nullable=False,
    )
    data = sa.Column(sa.JSON, nullable=False)
    created_by_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    reverted_at = sa.Column(sa.DateTime, nullable=True)


class NodePublishJob(Base):
    """
    Задание на отложенную публикацию контента, связанного с нодой.
    Храним и node_id (числовой PK из nodes), и content_id (BigInt из content_items),
    чтобы быстро резолвить обе стороны без UUID в контексте нод.
    """

    __tablename__ = "node_publish_jobs"

    id = sa.Column("id_bigint", sa.BigInteger, primary_key=True)
    node_id = sa.Column(sa.BigInteger, sa.ForeignKey("nodes.id"), nullable=False, index=True)
    content_id = sa.Column(
        sa.BigInteger,
        sa.ForeignKey("content_items.id_bigint"),
        nullable=False,
        index=True,
    )
    access = sa.Column(
        sa.String, nullable=False, default="everyone"
    )  # everyone|premium_only|early_access
    scheduled_at = sa.Column(sa.DateTime, nullable=False, index=True)
    status = sa.Column(
        sa.String, nullable=False, default="pending", index=True
    )  # pending|running|done|canceled|failed
    error = sa.Column(sa.Text, nullable=True)
    created_by_user_id = sa.Column(UUID(), sa.ForeignKey("users.id"), nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    executed_at = sa.Column(sa.DateTime, nullable=True)

