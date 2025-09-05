from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.system_models import AIDefaultModel

SINGLETON_ID = 1


class AIDefaultModelRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_default(self) -> AIDefaultModel | None:
        result = await self._db.execute(
            select(AIDefaultModel).where(AIDefaultModel.id == SINGLETON_ID)
        )
        return result.scalar_one_or_none()

    async def set_default(
        self, *, provider: str | None = None, model: str | None = None
    ) -> AIDefaultModel:
        row = await self.get_default()
        if row is None:
            row = AIDefaultModel(id=SINGLETON_ID, provider=provider, model=model)
            self._db.add(row)
        else:
            row.provider = provider
            row.model = model
        await self._db.flush()
        return row
