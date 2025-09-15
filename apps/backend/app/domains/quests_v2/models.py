from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.types import JSON

from app.providers.db.base import Base
from app.providers.db.sa_adapters import UUID as GUID


class QuestV2(Base):
    __tablename__ = "quests_v2"

    id = Column(GUID(), primary_key=True, default=uuid4)
    author_id = Column(GUID(), nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    tags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

