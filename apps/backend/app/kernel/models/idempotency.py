from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.kernel.db import Base, UUID


class IdempotencyKey(Base):
    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


__all__ = ["IdempotencyKey"]

