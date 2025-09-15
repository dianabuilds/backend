from __future__ import annotations

from typing import Protocol

from apps.backendDDD.domains.platform.telemetry.domain.generation import (
    GenerationStageLog,
)


class IGenerationLogRepository(Protocol):
    async def add_stage(self, entry: GenerationStageLog) -> None: ...


__all__ = ["IGenerationLogRepository"]
