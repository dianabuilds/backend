from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from app.core.db.adapters import JSONB, UUID
from app.core.db.base import Base


class JobStatus(str):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


class GenerationJob(Base):
    __tablename__ = "ai_generation_jobs"
    __table_args__ = (
        Index("ix_ai_generation_jobs_status_created_at", "status", "created_at"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)

    # Кто создал задание
    created_by = Column(UUID(), nullable=True)

    # Параметры генерации
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    params = Column(JSON, nullable=False, default=dict)

    # Статусы и время
    status = Column(String, default=JobStatus.queued, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Результаты
    result_quest_id = Column(UUID(), nullable=True)
    result_version_id = Column(UUID(), nullable=True)

    # Учёт стоимости/токенов
    cost = Column(Float, nullable=True)
    token_usage = Column(JSON, nullable=True)

    # Признак использования кэша (результат переиспользован)
    reused = Column(Boolean, default=False)

    # Прогресс и логи
    progress = Column(Integer, default=0)  # 0..100
    logs = Column(JSON, nullable=True, default=list)

    # Ошибки
    error = Column(Text, nullable=True)


class GenerationJobLog(Base):
    __tablename__ = "generation_job_logs"

    id = Column(UUID(), primary_key=True, default=uuid4)
    job_id = Column(UUID(), nullable=False, index=True)

    stage = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)

    prompt = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    raw_url = Column(Text, nullable=True)
    raw_preview = Column(Text, nullable=True)
    usage = Column(JSONB, nullable=True)
    cost = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="ok")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
