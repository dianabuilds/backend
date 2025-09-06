from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    timezone = Column(String, nullable=True)
    locale = Column(String, nullable=True)
    links = Column(JSONB, nullable=False, server_default=text("'{}'"))
    preferences = Column(JSONB, nullable=False, server_default=text("'{}'"))


__all__ = ["UserProfile"]
