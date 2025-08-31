from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.generation_models import GenerationJobLog
from app.domains.telemetry.application.ports.generation_log_port import (
    IGenerationLogRepository,
)
from app.domains.telemetry.domain.generation import GenerationStageLog


class GenerationLogRepository(IGenerationLogRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_stage(self, entry: GenerationStageLog) -> None:
        model = GenerationJobLog(
            job_id=entry.job_id,
            stage=entry.stage,
            provider=entry.provider,
            model=entry.model,
            prompt=entry.prompt,
            raw_response=entry.raw_response,
            usage=entry.usage,
            cost=float(entry.cost),
            status=entry.status,
        )
        self._db.add(model)
        await self._safe_flush()

    async def _safe_flush(self) -> None:
        try:
            await self._db.flush()
        except Exception:
            # Не мешаем основному флоу (совместимо со старой логикой)
            pass
