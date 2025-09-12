from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_prices_repository import (
    AIModelPriceRepository,
)
from app.kernel.db import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role)]


@router.get("/prices")
async def list_prices(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    repo = AIModelPriceRepository(db)
    rows = await repo.list_prices()
    return [r.as_dict() for r in rows]


@router.post("/prices")
async def add_price(
    payload: dict[str, Any],
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = AIModelPriceRepository(db)
    row = await repo.upsert_price(
        model=payload.get("model"),
        input_cost=payload.get("input_cost"),
        output_cost=payload.get("output_cost"),
        currency=payload.get("currency"),
    )
    return row.as_dict()

