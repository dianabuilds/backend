from __future__ import annotations

from typing import Any

from apps.backendDDD.domains.platform.telemetry.domain.generation import (
    GenerationStageLog,
)
from apps.backendDDD.domains.platform.telemetry.ports.generation_log_port import (
    IGenerationLogRepository,
)

_MAX_RAW = 30_000
_MAX_PROMPT = 8_000


class GenerationLogService:
    def __init__(self, repo: IGenerationLogRepository) -> None:
        self._repo = repo

    async def save_stage_log(
        self,
        *,
        job_id: Any,
        stage: str,
        provider: str,
        model: str,
        prompt: str,
        raw_response: str,
        usage: dict[str, int],
        cost: float,
        status: str = "ok",
    ) -> None:
        safe_prompt = (prompt or "")[:_MAX_PROMPT]
        safe_raw = (raw_response or "")[:_MAX_RAW]
        entry = GenerationStageLog(
            job_id=job_id,
            stage=stage,
            provider=provider,
            model=model,
            prompt=safe_prompt,
            raw_response=safe_raw,
            usage=usage,
            cost=float(cost),
            status=status,
        )
        await self._repo.add_stage(entry)


__all__ = ["GenerationLogService"]
