from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.system_models import AIModelPrice


class AIModelPriceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_prices(self) -> list[AIModelPrice]:
        result = await self._db.execute(select(AIModelPrice))
        return list(result.scalars())

    async def upsert_price(
        self,
        *,
        model: str,
        input_cost: float | None = None,
        output_cost: float | None = None,
        currency: str | None = None,
    ) -> AIModelPrice:
        result = await self._db.execute(select(AIModelPrice).where(AIModelPrice.model == model))
        row = result.scalar_one_or_none()
        if row is None:
            row = AIModelPrice(
                model=model,
                input_cost=input_cost,
                output_cost=output_cost,
                currency=currency,
            )
            self._db.add(row)
        else:
            row.input_cost = input_cost
            row.output_cost = output_cost
            row.currency = currency
        await self._db.flush()
        return row
