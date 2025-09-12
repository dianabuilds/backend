from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.kernel.db import Base, JSONB, UUID


class OutboxStatus(str, Enum):
    NEW = "NEW"
    SENT = "SENT"
    FAILED = "FAILED"


class OutboxEvent(Base):
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dedup_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default=OutboxStatus.NEW.value, nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[datetime] = mapped_column(nullable=False)
    tenant_id: Mapped[Optional[Any]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_preview: Mapped[bool] = mapped_column(default=False, nullable=False)


__all__ = ["OutboxEvent", "OutboxStatus"]

