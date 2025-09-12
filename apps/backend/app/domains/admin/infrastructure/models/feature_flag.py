from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy import Enum as SAEnum

from app.kernel.db import Base


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    key = Column(String, primary_key=True)
    value = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)
    audience = Column(
        SAEnum("all", "premium", "beta", name="feature_flag_audience"),
        nullable=False,
        default="all",
        server_default="all",
    )
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String, nullable=True)  # user id (string/uuid) as text

