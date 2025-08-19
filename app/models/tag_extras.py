from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from . import Base
from .adapters import UUID, JSONB


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
    report = Column(JSONB, nullable=True)  # агрегированный отчёт (counters_before/after, content_touched и т.д.)


class TagBlacklist(Base):
    __tablename__ = "tag_blacklist"

    slug = Column(String, primary_key=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
