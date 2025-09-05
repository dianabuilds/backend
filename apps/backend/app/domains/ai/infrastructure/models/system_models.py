from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.providers.db.base import Base


class AISystemModel(Base):
    __tablename__ = "ai_system_models"

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    provider = Column(String, nullable=True)
    name = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "provider": self.provider,
            "name": self.name,
            "active": bool(self.active),
        }


class AIModelPrice(Base):
    __tablename__ = "ai_model_prices"

    id = Column(Integer, primary_key=True)
    model = Column(String, nullable=False, index=True)
    input_cost = Column(Float, nullable=True)
    output_cost = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "model": self.model,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "currency": self.currency,
        }


class AIDefaultModel(Base):
    __tablename__ = "ai_model_defaults"

    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "model": self.model,
        }
