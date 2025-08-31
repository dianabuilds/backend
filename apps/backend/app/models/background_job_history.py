from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, String, func

from . import Base
from .adapters import UUID


class BackgroundJobHistory(Base):
    """History of background job executions."""

    __tablename__ = "background_job_history"

    id = Column(UUID(), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    log_url = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    finished_at = Column(DateTime, nullable=True)
