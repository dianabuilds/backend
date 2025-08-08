from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text

from .adapters import UUID
from . import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(), primary_key=True, default=uuid4)
    node_id = Column(UUID(), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_hidden = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=False)
