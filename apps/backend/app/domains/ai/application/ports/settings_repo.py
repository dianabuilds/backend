from __future__ import annotations

from typing import Any, Protocol

from app.domains.ai.infrastructure.models.ai_settings import AISettings


class IAISettingsRepository(Protocol):
    async def get_singleton(
        self, *, create_if_missing: bool, defaults: dict[str, Any]
    ) -> AISettings:  # pragma: no cover
        ...

    async def flush(self, row: AISettings | None = None) -> None:  # pragma: no cover
        ...
