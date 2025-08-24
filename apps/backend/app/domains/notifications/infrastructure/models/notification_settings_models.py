from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime

from app.core.db.adapters import UUID
from app.core.db.base import Base


class NodeNotificationSetting(Base):
    """Notification preferences for a node per user."""

    __tablename__ = "node_notification_settings"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), nullable=False)
    node_id = Column(UUID(), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
