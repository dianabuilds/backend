from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, Float, JSON, Boolean, Integer
from sqlalchemy.orm import relationship

from . import Base
from .adapters import UUID


class JobStatus(str):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


class GenerationJob(Base):
    __tablename__ = "ai_generation_jobs"

    id = Column(UUID(), primary_key=True, default=uuid4)

    # Кто создал задание
    created_by = Column(UUID(), nullable=True)

    # Параметры генерации
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    params = Column(JSON, nullable=False, default=dict)  # world_template_id, structure, length, tone, genre, locale, etc.

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
    token_usage = Column(JSON, nullable=True)  # {prompt_tokens, completion_tokens, ...}

    # Признак использования кэша (результат переиспользован)
    reused = Column(Boolean, default=False)

    # Прогресс и логи
    progress = Column(Integer, default=0)  # 0..100
    logs = Column(JSON, nullable=True, default=list)  # список строк/сообщений

    # Ошибки
    error = Column(Text, nullable=True)
