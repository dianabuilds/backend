from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String

from app.kernel.db import UUID, Base


class AIUsage(Base):
    __tablename__ = "ai_usage"
    __table_args__ = (
        Index("ix_ai_usage_profile_id", "profile_id"),
        Index("ix_ai_usage_user_id", "user_id"),
        Index("ix_ai_usage_ts", "ts"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    profile_id = Column(UUID(), nullable=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)

    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=True)

