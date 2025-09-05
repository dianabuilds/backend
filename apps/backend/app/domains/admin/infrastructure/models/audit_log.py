from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String

from app.providers.db.adapters import JSONB, UUID
from app.providers.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(), primary_key=True, default=uuid4)
    actor_id = Column(UUID(), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    workspace_id = Column(UUID(), nullable=True, index=True)
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSONB, nullable=True)
