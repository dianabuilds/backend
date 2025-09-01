from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Text

from app.core.db.adapters import UUID
from app.core.db.base import Base


class UserRestriction(Base):
    __tablename__ = "user_restrictions"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    type = Column(Enum("ban", "post_restrict", name="restriction_type"), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    issued_by = Column(UUID(), ForeignKey("users.id"))


class ContentModeration(Base):
    __tablename__ = "node_moderation"

    id = Column(UUID(), primary_key=True, default=uuid4)
    node_id = Column(BigInteger, ForeignKey("nodes.id"))
    reason = Column(Text)
    hidden_by = Column(UUID(), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
