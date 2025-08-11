from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.ext.mutable import MutableDict

from . import Base
from .adapters import UUID, JSONB


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(), primary_key=True, default=uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    source = Column(
        SAEnum("manual", "webhook", name="payment_source"),
        nullable=False,
    )
    days = Column(Integer, nullable=False)
    status = Column(
        SAEnum("pending", "confirmed", "failed", "cancelled", name="payment_status"),
        default="pending",
        nullable=False,
    )
    payload = Column(MutableDict.as_mutable(JSONB), default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
