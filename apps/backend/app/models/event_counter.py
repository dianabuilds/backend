from sqlalchemy import Column, ForeignKey, Integer, String

from . import Base
from .adapters import UUID


class UserEventCounter(Base):
    """Persistent counter for user events used in achievement tracking."""

    __tablename__ = "user_event_counters"

    workspace_id = Column(
        UUID(), ForeignKey("workspaces.id"), primary_key=True, index=True
    )
    user_id = Column(
        UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    event = Column(String, primary_key=True)
    count = Column(Integer, default=0, nullable=False)
