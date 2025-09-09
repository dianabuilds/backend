from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.providers.db.base import Base
from app.schemas.nodes_common import Status, Visibility


class WorldTemplate(Base):
    __tablename__ = "world_templates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Profile-centric scope only
    profile_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    title = Column(String, nullable=False)
    locale = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)

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
    created_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    characters = relationship("Character", back_populates="world", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    world_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("world_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    traits = Column(JSON, nullable=True)

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
    created_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    world = relationship("WorldTemplate", back_populates="characters")
