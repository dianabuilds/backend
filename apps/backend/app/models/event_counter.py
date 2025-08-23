from sqlalchemy import Column, Integer, String, ForeignKey

from . import Base
from .adapters import UUID


class UserEventCounter(Base):
    """Persistent counter for user events used in achievement tracking."""

    __tablename__ = "user_event_counters"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    event = Column(String, primary_key=True)
    count = Column(Integer, default=0, nullable=False)
