from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
import sqlalchemy as sa
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.providers.db.adapters import UUID
from app.providers.db.base import Base
from app.schemas.nodes_common import Status, Visibility


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(UUID(), primary_key=True, default=uuid4)
    # account_id column was removed from the DB. Keep a transient attribute for legacy reads.
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    condition = Column(JSON, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)
    status = Column(
        SAEnum(Status, name="content_status"),
        nullable=False,
        server_default=Status.draft.value,
    )
    version = Column(Integer, nullable=False, server_default="1")
    visibility = Column(
        SAEnum(Visibility, name="content_visibility"),
        nullable=False,
        server_default=Visibility.private.value,
    )
    created_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)

    users = relationship("UserAchievement", back_populates="achievement")

    def __init__(self, **kwargs):  # type: ignore[override]
        acc = kwargs.pop("account_id", None)
        if acc is not None:
            try:
                object.__setattr__(self, "_legacy_account_id", acc)
            except Exception:
                pass
        super().__init__(**kwargs)

    @property
    def account_id(self) -> int | None:  # type: ignore[override]
        return getattr(self, "_legacy_account_id", None)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(
        UUID(), ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True
    )
    # account_id column was removed; keep transient attribute only
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    achievement = relationship("Achievement", back_populates="users")

    def __init__(self, **kwargs):  # type: ignore[override]
        acc = kwargs.pop("account_id", None)
        if acc is not None:
            try:
                object.__setattr__(self, "_legacy_account_id", acc)
            except Exception:
                pass
        super().__init__(**kwargs)

    @property
    def account_id(self) -> int | None:  # type: ignore[override]
        return getattr(self, "_legacy_account_id", None)
