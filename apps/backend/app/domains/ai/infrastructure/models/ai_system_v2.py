from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.providers.db.base import Base


class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    manifest = Column(JSONB, nullable=True)
    health = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")


class AIProviderSecret(Base):
    __tablename__ = "ai_provider_secrets"

    provider_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_providers.id", ondelete="CASCADE"), primary_key=True
    )
    key = Column(String, primary_key=True)
    # Store as text for now; can be migrated to encrypted storage later
    value_encrypted = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIModel(Base):
    __tablename__ = "ai_models"
    __table_args__ = (UniqueConstraint("provider_id", "code", name="uq_ai_models_provider_code"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False
    )
    code = Column(String, nullable=False)
    name = Column(String, nullable=True)
    family = Column(String, nullable=True)
    capabilities = Column(JSONB, nullable=True)
    inputs = Column(JSONB, nullable=True)
    limits = Column(JSONB, nullable=True)
    pricing = Column(JSONB, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)

    provider = relationship("AIProvider", back_populates="models")


class AIDefaults(Base):
    __tablename__ = "ai_defaults"

    # singleton row
    id = Column(String, primary_key=True, default="1")
    provider_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True
    )
    model_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True
    )
    bundle_id = Column(UUID(as_uuid=True), nullable=True)


class AIRoutingProfile(Base):
    __tablename__ = "ai_routing_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    rules = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIPreset(Base):
    __tablename__ = "ai_presets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    task = Column(String, nullable=False)
    params = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIEvalRun(Base):
    __tablename__ = "ai_eval_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_routing_profiles.id", ondelete="SET NULL"), nullable=True
    )
    spec = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="queued")
    stats = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
