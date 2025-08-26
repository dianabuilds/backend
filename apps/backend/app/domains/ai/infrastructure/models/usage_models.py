from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy import Index

from app.core.db.base import Base
from app.core.db.adapters import UUID


class AIUsage(Base):
    __tablename__ = "ai_usage"
    __table_args__ = (
        Index("ix_ai_usage_workspace_id", "workspace_id"),
        Index("ix_ai_usage_user_id", "user_id"),
        Index("ix_ai_usage_ts", "ts"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)

    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=True)

