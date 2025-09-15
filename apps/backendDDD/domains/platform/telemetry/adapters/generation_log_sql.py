from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backendDDD.domains.platform.telemetry.domain.generation import (
    GenerationStageLog,
)
from apps.backendDDD.domains.platform.telemetry.ports.generation_log_port import (
    IGenerationLogRepository,
)


class GenerationLogSQLRepository(IGenerationLogRepository):
    """SQL repository writing into `generation_job_logs` (legacy-compatible)."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def add_stage(self, entry: GenerationStageLog) -> None:
        sql = text(
            """
            INSERT INTO generation_job_logs(
              job_id, stage, provider, model, prompt, raw_response,
              usage, cost, status, created_at
            ) VALUES (
              :job_id, :stage, :provider, :model, :prompt, :raw_response,
              cast(:usage as jsonb), :cost, :status, now()
            )
            """
        )
        params = {
            "job_id": entry.job_id,
            "stage": entry.stage,
            "provider": entry.provider,
            "model": entry.model,
            "prompt": entry.prompt,
            "raw_response": entry.raw_response,
            "usage": entry.usage,
            "cost": float(entry.cost) if entry.cost is not None else None,
            "status": entry.status,
        }
        async with self._engine.begin() as conn:
            await conn.execute(sql, params)


__all__ = ["GenerationLogSQLRepository"]
