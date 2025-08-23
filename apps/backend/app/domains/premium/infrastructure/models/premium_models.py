from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.core.db.adapters import UUID, JSONB


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (UniqueConstraint("slug", name="uq_plan_slug"),)

    id = Column(UUID(), primary_key=True, default=uuid4)
    slug = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price_cents = Column(Integer, nullable=True)
    currency = Column(String, nullable=True, default="USD")
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=100)
    monthly_limits = Column(JSONB, nullable=True)
    features = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    subscriptions = relationship("UserSubscription", back_populates="plan", cascade="all, delete-orphan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(UUID(), ForeignKey("subscription_plans.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="active")
    auto_renew = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
