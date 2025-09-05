from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.core.db.base import Base


class AISettings(Base):
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    model = Column(String, nullable=True)
    model_map = Column(JSON, nullable=True)
    cb = Column(JSON, nullable=True)
    has_api_key = Column(Boolean, default=False)
    api_key = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "model_map": self.model_map,
            "cb": self.cb,
            "has_api_key": bool(self.has_api_key),
        }
