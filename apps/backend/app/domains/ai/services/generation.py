"""
Domains.AI: Generation services (реализация).

Публичный контракт:
- enqueue_generation_job(db, *, created_by, params, provider?, model?, reuse?=True)
  -> GenerationJob
- process_next_generation_job(db) -> UUID | None
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.preview import PreviewContext
from app.domains.ai.infrastructure.models.generation_models import (
    GenerationJob,
    JobStatus,
)


async def _merge_generation_settings(
    db: AsyncSession,
    *,
    params: dict[str, Any],
    provider: str | None,
    model: str | None,
    workspace_id: UUID | None,
) -> tuple[dict[str, Any], str | None, str | None, dict[str, dict[str, Any]]]:
    """Merge explicit params, workspace overrides and global AI settings.

    Returns updated (params, provider, model, trace).
    """

    from app.domains.ai.infrastructure.models.ai_settings import AISettings
    from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
    from app.schemas.workspaces import WorkspaceSettings

    trace: dict[str, dict[str, Any]] = {}
    orig_provider, orig_model = provider, model
    orig_params = dict(params)

    def _set(key: str, value: Any, source: str) -> None:
        nonlocal provider, model
        if key == "provider":
            provider = value
        elif key == "model":
            model = value
        else:
            params[key] = value
        trace[key] = {"value": value, "source": source}

    # 1) Global settings
    try:
        res = await db.execute(select(AISettings).limit(1))
        ai = res.scalars().first()
        if ai:
            if ai.provider:
                _set("provider", ai.provider, "global")
            if ai.model:
                _set("model", ai.model, "global")
    except Exception:
        pass

    # 2) Workspace overrides
    if workspace_id is not None:
        try:
            ws = await WorkspaceDAO.get(db, workspace_id)
            if ws:
                settings = WorkspaceSettings.model_validate(ws.settings_json)
                presets = settings.ai_presets or {}
                params.setdefault("workspace_id", str(workspace_id))
                for key in ("provider", "model", "temperature", "system_prompt", "forbidden"):
                    if key in presets and presets[key] is not None and key not in params:
                        _set(key, presets[key], "workspace")
        except Exception:
            pass

    # 3) Explicit request values override
    if orig_provider is not None:
        _set("provider", orig_provider, "explicit")
    if orig_model is not None:
        _set("model", orig_model, "explicit")
    for key in ("temperature", "system_prompt", "forbidden"):
        if key in orig_params:
            _set(key, params.get(key), "explicit")

    return params, provider, model, trace

logger = logging.getLogger(__name__)


async def enqueue_generation_job(
    db: AsyncSession,
    *,
    created_by: UUID | None,
    params: dict[str, Any],
    provider: str | None = None,
    model: str | None = None,
    workspace_id: UUID | None = None,
    reuse: bool = True,
    preview: PreviewContext | None = None,
) -> GenerationJob:
    """Создать задание на генерацию ИИ‑квеста и поставить в очередь.
    Если reuse=True и уже есть завершённая задача с идентичными параметрами — создаём
    мгновенно завершённую job, переиспользуя result_quest_id/cost/token_usage.
    """
    params = dict(params)
    params, provider, model, trace = await _merge_generation_settings(
        db,
        params=params,
        provider=provider,
        model=model,
        workspace_id=workspace_id,
    )

    if reuse:
        # Ищем последнюю завершённую задачу с такими же параметрами
        res = await db.execute(
            select(GenerationJob)
            .where(
                GenerationJob.status == JobStatus.completed,
                GenerationJob.params == params,
            )
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
                logs=[{"applied": trace}],
            )
            db.add(job)
            await db.flush()
            return job

    # Обычная постановка в очередь: списываем квоту ai_generations
    # (если известен пользователь)
    if created_by is not None:
        try:
            from app.domains.premium.quotas import check_and_consume_quota

            await check_and_consume_quota(
                db,
                created_by,
                quota_key="ai_generations",
                amount=1,
                scope="month",
                preview=preview,
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
        logs=[{"applied": trace}],
    )
    db.add(job)
    await db.flush()  # чтобы получить id
    return job


async def process_next_generation_job(db: AsyncSession) -> UUID | None:
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
        from app.domains.telemetry.application.worker_metrics_facade import (
            worker_metrics,
        )

        worker_metrics.inc("started", 1)
    except Exception:
        pass
    _job_t0 = datetime.utcnow()

    try:
        # 3) Запускаем пайплайн
        from app.domains.ai.pipeline import run_full_generation

        result = await run_full_generation(db, job)
        # Ожидаем, что result содержит: result_quest_id, result_version_id,
        # cost, token_usage, logs, last_provider, last_model
        # Финализируем completed
        job.status = JobStatus.completed
        job.finished_at = datetime.utcnow()
        job.result_quest_id = result.get("result_quest_id")
        job.result_version_id = result.get("result_version_id")
        job.cost = float(result.get("cost", 0.0))
        job.token_usage = result.get("token_usage") or {}
        try:
            workspace_id = (job.params or {}).get("workspace_id")
            usage = (
                job.token_usage.get("total", {})
                if isinstance(job.token_usage, dict)
                else {}
            )
            tokens = int(usage.get("prompt", 0)) + int(usage.get("completion", 0))
            if workspace_id and job.created_by and tokens > 0:
                from app.domains.workspaces.limits import consume_workspace_limit

                limit_log: dict[str, Any] = {}
                allowed = await consume_workspace_limit(
                    db,
                    job.created_by,
                    workspace_id,
                    "ai_tokens",
                    amount=tokens,
                    scope="month",
                    degrade=True,
                    log=limit_log,
                    preview=preview,
                )
                if limit_log:
                    try:
                        job.logs.append({"limits": limit_log})
                    except Exception:
                        pass
                if not allowed:
                    job.status = JobStatus.failed
                    job.error = "AI tokens limit exceeded"
                    await db.flush()
                    await db.commit()
                    return job.id
        except Exception:
            pass
        # сохраняем логи и факт использованного провайдера/модели
        if hasattr(job, "logs"):
            existing = list(getattr(job, "logs", []) or [])
            new_logs = result.get("logs") or []
            existing.extend(new_logs)
            job.logs = existing  # type: ignore[attr-defined]
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
            from app.domains.telemetry.application.worker_metrics_facade import (
                worker_metrics,
            )

            worker_metrics.inc("completed", 1)
            if _job_t0:
                dt_ms = (datetime.utcnow() - _job_t0).total_seconds() * 1000.0
                worker_metrics.observe_duration(dt_ms)
            # учёт стоимости и токенов по задаче
            try:
                usage = (
                    result.get("token_usage", {}).get("total", {})
                    if isinstance(result, dict)
                    else {}
                )
                p = int(usage.get("prompt", 0))
                c = int(usage.get("completion", 0))
                worker_metrics.observe_job(
                    cost_usd=float(result.get("cost", 0.0) or 0.0),
                    prompt_tokens=p,
                    completion_tokens=c,
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
            from app.domains.telemetry.application.worker_metrics_facade import (
                worker_metrics,
            )

            worker_metrics.inc("failed", 1)
            if _job_t0:
                dt_ms = (datetime.utcnow() - _job_t0).total_seconds() * 1000.0
                worker_metrics.observe_duration(dt_ms)
        except Exception:
            pass
        return job.id


__all__ = ["enqueue_generation_job", "process_next_generation_job"]
