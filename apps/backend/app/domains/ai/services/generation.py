"""
Domains.AI: Generation services (реализация).

Публичный контракт:
- enqueue_generation_job(db, *, created_by, params, provider?, model?, reuse?=True) -> GenerationJob
- process_next_generation_job(db) -> Optional[UUID]
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.ai.infrastructure.models.generation_models import GenerationJob, JobStatus

logger = logging.getLogger(__name__)


async def enqueue_generation_job(
    db: AsyncSession,
    *,
    created_by: Optional[UUID],
    params: dict[str, Any],
    provider: str | None = None,
    model: str | None = None,
    workspace_id: UUID | None = None,
    reuse: bool = True,
) -> GenerationJob:
    """Создать задание на генерацию ИИ‑квеста и поставить в очередь.
    Если reuse=True и уже есть завершённая задача с идентичными параметрами — создаём
    мгновенно завершённую job, переиспользуя result_quest_id/cost/token_usage.
    """
    params = dict(params)
    if workspace_id is not None:
        try:
            from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
            from app.schemas.workspaces import WorkspaceSettings

            ws = await WorkspaceDAO.get(db, workspace_id)
            if ws:
                settings = WorkspaceSettings.model_validate(ws.settings_json)
                presets = settings.ai_presets or {}
                params.setdefault("workspace_id", str(workspace_id))
                if model is None and isinstance(presets.get("model"), str):
                    model = presets["model"]
                for key in ("temperature", "system_prompt", "forbidden"):
                    if key in presets and key not in params:
                        params[key] = presets[key]
        except Exception:
            pass

    if reuse:
        # Ищем последнюю завершённую задачу с такими же параметрами
        res = await db.execute(
            select(GenerationJob)
            .where(GenerationJob.status == JobStatus.completed, GenerationJob.params == params)
            .order_by(GenerationJob.finished_at.desc())
        )
        cached = res.scalars().first()
        if cached:
            job = GenerationJob(
                created_by=created_by,
                provider=provider or cached.provider,
                model=model or cached.model,
                params=params,
                status=JobStatus.completed,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                result_quest_id=cached.result_quest_id,
                result_version_id=cached.result_version_id,
                cost=cached.cost,
                token_usage=cached.token_usage,
                reused=True,
                error=None,
            )
            db.add(job)
            await db.flush()
            return job

    # Обычная постановка в очередь: списываем квоту ai_generations (если известен пользователь)
    if created_by is not None:
        try:
            from app.domains.premium.quotas import check_and_consume_quota
            await check_and_consume_quota(
                db, created_by, quota_key="ai_generations", amount=1, scope="month", dry_run=False
            )
        except Exception:
            # Если квота превышена — исключение уйдёт вверх и API вернёт 429
            raise

    job = GenerationJob(
        created_by=created_by,
        provider=provider,
        model=model,
        params=params,
        status=JobStatus.queued,
    )
    db.add(job)
    await db.flush()  # чтобы получить id
    return job


async def process_next_generation_job(db: AsyncSession) -> Optional[UUID]:
    """Забрать одну queued-задачу, безопасно перевести в running и выполнить пайплайн.
    Возвращает id обработанной задачи или None, если очереди нет.
    """
    # 1) Пытаемся захватить одну queued-задачу (skip locked)
    res = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.status == JobStatus.queued)
        .order_by(GenerationJob.created_at.asc())
        .with_for_update(skip_locked=True)
    )
    job = res.scalars().first()
    if not job:
        return None

    # 2) Переводим в running
    job.status = JobStatus.running
    job.started_at = datetime.utcnow()
    await db.flush()
    await db.commit()  # фиксируем захват, освобождаем блокировку строки

    # метрики воркера
    try:
        from app.domains.telemetry.application.worker_metrics_facade import worker_metrics
        worker_metrics.inc("started", 1)
    except Exception:
        pass
    _job_t0 = datetime.utcnow()

    try:
        # 3) Загружаем пресеты рабочей области при необходимости
        params = job.params or {}
        workspace_id = params.get("workspace_id")
        if workspace_id:
            try:
                from uuid import UUID
                from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
                from app.schemas.workspaces import WorkspaceSettings

                ws = await WorkspaceDAO.get(db, UUID(workspace_id))
                if ws:
                    settings = WorkspaceSettings.model_validate(ws.settings_json)
                    presets = settings.ai_presets or {}
                    if job.model is None and isinstance(presets.get("model"), str):
                        job.model = presets["model"]
                    for key in ("temperature", "system_prompt", "forbidden"):
                        if key in presets and key not in params:
                            params[key] = presets[key]
                    job.params = params
                    await db.flush()
            except Exception:
                pass

        # 4) Запускаем пайплайн
        from app.domains.ai.pipeline import run_full_generation

        result = await run_full_generation(db, job)
        # Ожидаем, что result содержит: result_quest_id, result_version_id, cost, token_usage, logs, last_provider, last_model
        # Финализируем completed
        job.status = JobStatus.completed
        job.finished_at = datetime.utcnow()
        job.result_quest_id = result.get("result_quest_id")
        job.result_version_id = result.get("result_version_id")
        job.cost = float(result.get("cost", 0.0))
        job.token_usage = result.get("token_usage") or {}
        # сохраняем логи и факт использованного провайдера/модели
        if hasattr(job, "logs"):
            job.logs = result.get("logs")  # type: ignore[attr-defined]
        if "last_provider" in result and result.get("last_provider"):
            job.provider = result.get("last_provider")
        if "last_model" in result and result.get("last_model"):
            job.model = result.get("last_model")
        # завершаем прогресс
        try:
            job.progress = 100
        except Exception:
            pass
        job.error = None
        await db.flush()
        await db.commit()
        try:
            from app.domains.telemetry.application.worker_metrics_facade import worker_metrics
            worker_metrics.inc("completed", 1)
            if _job_t0:
                dt_ms = (datetime.utcnow() - _job_t0).total_seconds() * 1000.0
                worker_metrics.observe_duration(dt_ms)
            # учёт стоимости и токенов по задаче
            try:
                usage = result.get("token_usage", {}).get("total", {}) if isinstance(result, dict) else {}
                p = int(usage.get("prompt", 0))
                c = int(usage.get("completion", 0))
                worker_metrics.observe_job(
                    cost_usd=float(result.get("cost", 0.0) or 0.0), prompt_tokens=p, completion_tokens=c
                )
            except Exception:
                pass
        except Exception:
            pass
        logger.info("Generation job %s completed", job.id)
        return job.id
    except Exception as e:
        # 5) Отмечаем failed
        logger.exception("Generation job %s failed: %s", job.id, e)
        # 6) Откатываем любые незакоммиченные изменения пайплайна и помечаем job
        await db.rollback()
        await db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job.id)
            .values(
                status=JobStatus.failed,
                finished_at=datetime.utcnow(),
                error=str(e),
            )
        )
        await db.commit()
        try:
            from app.domains.telemetry.application.worker_metrics_facade import worker_metrics
            worker_metrics.inc("failed", 1)
            if _job_t0:
                dt_ms = (datetime.utcnow() - _job_t0).total_seconds() * 1000.0
                worker_metrics.observe_duration(dt_ms)
        except Exception:
            pass
        return job.id


__all__ = ["enqueue_generation_job", "process_next_generation_job"]
