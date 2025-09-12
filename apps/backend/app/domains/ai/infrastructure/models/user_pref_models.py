from __future__ import annotations

from sqlalchemy import Column, String

from app.kernel.db import UUID, Base


class UserAIPref(Base):
    __tablename__ = "user_ai_pref"

    user_id = Column(UUID(), primary_key=True)
    model = Column(String, nullable=False)


__all__ = ["UserAIPref"]

