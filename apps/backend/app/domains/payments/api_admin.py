from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import cast
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.payments.infrastructure.models.payment_models import PaymentTransaction
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/payments",
    tags=["admin-payments"],
    responses=cast(dict[int | str, dict[str, object]], ADMIN_AUTH_RESPONSES),
)

admin_required = require_admin_role({"admin"})


class RecentPayment(BaseModel):
    id: UUID
    user_id: UUID
    tariff: str | None
    amount: int
    status: str


@router.get(
    "/recent", response_model=list[RecentPayment], summary="List recent payments"
)
async def list_recent_payments(
    limit: int = 20,
    _=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[RecentPayment]:
    stmt = (
        select(PaymentTransaction)
        .order_by(PaymentTransaction.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    txs = res.scalars().all()
    return [
        RecentPayment(
            id=cast(UUID, tx.id),
            user_id=cast(UUID, tx.user_id),
            tariff=cast(str | None, tx.product_type),
            amount=cast(int, tx.gross_cents),
            status=cast(str, tx.status),
        )
        for tx in txs
    ]
