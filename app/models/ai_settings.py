from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer

from app.db.base import Base


class AISettings(Base):
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, default=1)
    provider = Column(String, nullable=True)
    base_url = Column(Text, nullable=True)
    model = Column(String, nullable=True)
    api_key = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
