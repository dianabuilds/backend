from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON

from app.db.base import Base
from app.core.db.adapters import UUID


class CampaignStatus(str):
    queued = "queued"
    running = "running"
    done = "done"
    canceled = "canceled"
    failed = "failed"


class NotificationCampaign(Base):
    __tablename__ = "notification_campaigns"

    id = Column(UUID(), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False, default="system")
    filters = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default=CampaignStatus.queued)
    total = Column(Integer, nullable=False, default=0)
    sent = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    created_by = Column(UUID(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
