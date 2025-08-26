from __future__ import annotations

from sqlalchemy import Column, String

from app.core.db.base import Base
from app.core.db.adapters import UUID


class UserAIPref(Base):
    __tablename__ = "user_ai_pref"

    user_id = Column(UUID(), primary_key=True)
    model = Column(String, nullable=False)


__all__ = ["UserAIPref"]
