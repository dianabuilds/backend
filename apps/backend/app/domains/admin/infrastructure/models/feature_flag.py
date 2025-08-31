from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.db.base import Base


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    key = Column(String, primary_key=True)
    value = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, nullable=True)  # user id (string/uuid) as text
