from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from app.providers.db.adapters import JSONB, UUID
from app.providers.db.base import Base


class PaymentGatewayConfig(Base):
    __tablename__ = "payment_gateways"
    __table_args__ = (UniqueConstraint("slug", name="uq_payment_gateway_slug"),)

    id = Column(UUID(), primary_key=True, default=uuid4)
    slug = Column(String, nullable=False)
    type = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    config = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), nullable=False, index=True)
    gateway_slug = Column(String, nullable=True, index=True)

    product_type = Column(String, nullable=False)  # quest_purchase | subscription | ...
    product_id = Column(UUID(), nullable=True, index=True)

    currency = Column(String, nullable=True, default="USD")
    gross_cents = Column(Integer, nullable=False)
    fee_cents = Column(Integer, nullable=False, default=0)
    net_cents = Column(Integer, nullable=False)

    status = Column(
        String, nullable=False, default="captured"
    )  # authorized|captured|settled|refunded
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    meta = Column(JSONB, nullable=True)
