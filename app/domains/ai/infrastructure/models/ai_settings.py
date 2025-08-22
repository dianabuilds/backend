from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime

from app.core.db.base import Base
from app.core.db.adapters import UUID


class AISettings(Base):
    __tablename__ = "ai_settings"

    id = Column(UUID(), primary_key=True, default=uuid4)
    provider = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    model = Column(String, nullable=True)
    api_key = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
