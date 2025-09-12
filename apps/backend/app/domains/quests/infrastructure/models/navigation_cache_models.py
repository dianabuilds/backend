from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.ext.mutable import MutableDict, MutableList

from app.kernel.db import ARRAY, JSONB, UUID, Base


class NavigationCache(Base):
    __tablename__ = "navigation_cache"

    id = Column(UUID(), primary_key=True, default=uuid4)
    node_slug = Column(String, index=True, nullable=False)
    navigation = Column(MutableDict.as_mutable(JSONB), default=dict)
    compass = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    echo = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("node_slug", name="uq_nav_cache_slug"),
        Index("ix_navigation_cache_generated_at", "generated_at"),
    )

