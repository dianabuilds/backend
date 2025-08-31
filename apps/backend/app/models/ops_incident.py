from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, String, func

from . import Base
from .adapters import UUID


class OpsIncident(Base):
    """Operational incident such as HTTP 5xx error or task failure."""

    __tablename__ = "ops_incidents"

    id = Column(UUID(), primary_key=True, default=uuid4)
    kind = Column(String, nullable=False)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
