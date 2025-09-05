from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class NodeNotificationSetting(Base):
    """Notification preferences for a node per user."""

    __tablename__ = "node_notification_settings"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), nullable=False)
    node_id = Column(BigInteger, ForeignKey("nodes.id"), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# B-tree index on the new node_id column
Index("ix_node_notification_settings_node_id", NodeNotificationSetting.node_id)
