from __future__ import annotations

from typing import Protocol

from app.domains.telemetry.domain.generation import GenerationStageLog


class IGenerationLogRepository(Protocol):
    async def add_stage(
        self, entry: GenerationStageLog
    ) -> None:  # pragma: no cover - контракт
        ...
