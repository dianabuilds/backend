from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.system_models import AISystemModel


class AISystemModelRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_models(self) -> list[AISystemModel]:
        result = await self._db.execute(select(AISystemModel))
        return list(result.scalars())

    async def upsert_model(
        self,
        *,
        code: str,
        provider: str | None = None,
        name: str | None = None,
        active: bool = True,
    ) -> AISystemModel:
        result = await self._db.execute(select(AISystemModel).where(AISystemModel.code == code))
        row = result.scalar_one_or_none()
        if row is None:
            row = AISystemModel(
                code=code,
                provider=provider,
                name=name,
                active=active,
            )
            self._db.add(row)
        else:
            row.provider = provider
            row.name = name
            row.active = active
        await self._db.flush()
        return row
