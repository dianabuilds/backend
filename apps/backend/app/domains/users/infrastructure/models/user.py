from __future__ import annotations
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, String, Text

from app.core.db.base import Base
from app.core.db.adapters import UUID


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

    # GDPR
    deleted_at = Column(DateTime, nullable=True)
# Реэкспорт ORM-модели пользователя для доменного слоя users
from app.domains.users.infrastructure.models.user import User  # noqa: F401

__all__ = ["User"]
