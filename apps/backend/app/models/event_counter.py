from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String
import sqlalchemy as sa

from app.providers.db.base import Base

from .adapters import UUID


class UserEventCounter(Base):
    """Persistent counter for user events used in achievement tracking."""

    __tablename__ = "user_event_counters"

    # Legacy: scope id stored as text/sentinel (e.g., "0")
    account_id = Column(String, primary_key=True, index=True)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    event = Column(String, primary_key=True)
    count = Column(Integer, default=0, nullable=False)
