from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.application.ports.settings_repo import IAISettingsRepository
from app.domains.ai.infrastructure.models.ai_settings import AISettings

SINGLETON_ID = 1


class AISettingsRepository(IAISettingsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_singleton(
        self, *, create_if_missing: bool, defaults: dict[str, Any]
    ) -> AISettings:
        result = await self._db.execute(select(AISettings).where(AISettings.id == SINGLETON_ID))
        row = result.scalar_one_or_none()
        if row is None and create_if_missing:
            row = AISettings(
                id=SINGLETON_ID,
                provider=defaults.get("provider"),
                base_url=defaults.get("base_url"),
                model=defaults.get("model"),
                model_map=defaults.get("model_map"),
                cb=defaults.get("cb"),
                has_api_key=bool(defaults.get("has_api_key", False)),
                api_key=defaults.get("api_key"),
            )
            self._db.add(row)
            await self._db.flush()
        return row  # type: ignore[return-value]

    async def flush(self, row: AISettings | None = None) -> None:
        await self._db.flush()
