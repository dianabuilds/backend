from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy import Enum as SAEnum

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Auth
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    wallet_address = Column(String, unique=True, nullable=True)

    # Meta
    is_active = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    role = Column(
        SAEnum(
            "user",
            "moderator",
            "support",
            "admin",
            name="user_role",
        ),
        default="user",
        nullable=False,
    )

    # Profile
    username = Column(String, unique=True, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    default_workspace_id = Column(UUID(), nullable=True)

    # Activity
    last_login_at = Column(DateTime, nullable=True)

    # GDPR
    deleted_at = Column(DateTime, nullable=True)


__all__ = ["User"]
