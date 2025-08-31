from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.mutable import MutableDict, MutableList

from app.core.db.adapters import ARRAY, JSONB, UUID
from app.core.db.base import Base


class NavigationCache(Base):
    __tablename__ = "navigation_cache"

    id = Column(UUID(), primary_key=True, default=uuid4)
    node_slug = Column(String, unique=True, index=True, nullable=False)
    navigation = Column(MutableDict.as_mutable(JSONB), default=dict)
    compass = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    echo = Column(MutableList.as_mutable(ARRAY(String)), default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)
