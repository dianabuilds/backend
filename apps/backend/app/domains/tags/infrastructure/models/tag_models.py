from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import relationship

from app.providers.db.adapters import JSONB, UUID
from app.providers.db.base import Base


class NodeTag(Base):
    __tablename__ = "node_tags"

    node_id = Column(BigInteger, ForeignKey("nodes.id"), primary_key=True)
    tag_id = Column(UUID(), ForeignKey("tags.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TagAlias(Base):
    __tablename__ = "tag_aliases"

    id = Column(UUID(), primary_key=True, default=uuid4)
    tag_id = Column(UUID(), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = Column(String, unique=True, nullable=False, index=True)
    type = Column(String, nullable=False, default="synonym")  # synonym | misspelling
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tag = relationship("Tag")


class TagMergeLog(Base):
    __tablename__ = "tag_merge_logs"

    id = Column(UUID(), primary_key=True, default=uuid4)
    from_tag_id = Column(UUID(), nullable=False)
    to_tag_id = Column(UUID(), nullable=False)
    merged_by = Column(UUID(), nullable=True)
    merged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    dry_run = Column(Boolean, default=False, nullable=False)
    reason = Column(String, nullable=True)
    report = Column(JSONB, nullable=True)


class TagBlacklist(Base):
    __tablename__ = "tag_blacklist"

    slug = Column(String, primary_key=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TagUsageCounter(Base):
    __tablename__ = "tag_usage_counters"

    author_id = Column(UUID(), primary_key=True)
    content_type = Column(String, primary_key=True, default="node")
    slug = Column(String, primary_key=True)
    count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
