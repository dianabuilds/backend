from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, String, UniqueConstraint

from app.providers.db.adapters import UUID
from app.providers.db.base import Base


class SharedObject(Base):
    __tablename__ = "shared_objects"
    __table_args__ = (
        UniqueConstraint("object_type", "object_id", "profile_id", name="uq_shared_object"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    object_type = Column(String, nullable=False)
    object_id = Column(UUID(), nullable=False)
    profile_id = Column(UUID(), nullable=False, index=True)
    permissions = Column(String, nullable=False)
