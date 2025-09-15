from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class CampaignStatus(str):
    draft = "draft"
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
    type = Column(String, nullable=False, default="platform")
    filters = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default=CampaignStatus.draft)
    total = Column(Integer, nullable=False, default=0)
    sent = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    created_by = Column(UUID(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
