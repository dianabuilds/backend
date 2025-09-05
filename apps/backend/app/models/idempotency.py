from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String

from app.providers.db.base import Base


class IdempotencyKey(Base):
    """Stores processed idempotency keys for mutating requests."""

    __tablename__ = "idempotency_keys"

    key = Column(String, primary_key=True)
    fingerprint = Column(String, nullable=False)
    status = Column(Integer, nullable=True)
    response_sha256 = Column(String, nullable=True)
    payload_bytes = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
