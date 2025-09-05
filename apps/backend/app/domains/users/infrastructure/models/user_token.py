from __future__ import annotations

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class TokenAction(str, enum.Enum):
    verify = "verify"
    reset = "reset"


class UserToken(Base):
    __tablename__ = "user_tokens"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(Enum(TokenAction), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="tokens")
