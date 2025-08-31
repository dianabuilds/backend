from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db.session import get_db
from app.domains.payments.application.payments_service import PaymentService
from app.domains.users.infrastructure.models.user import User
from app.schemas.payment import PremiumPurchaseIn

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/premium", response_model=dict, summary="Buy premium")
async def buy_premium(
    payload: PremiumPurchaseIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade the current user to premium using a payment token."""
    amount = payload.days  # 1 token per day in this simplified example
    if not await PaymentService().verify(payload.payment_token, amount):
        raise HTTPException(status_code=400, detail="Payment not confirmed")

    now = datetime.utcnow()
    if current_user.premium_until and current_user.premium_until > now:
        current_user.premium_until += timedelta(days=payload.days)
    else:
        current_user.premium_until = now + timedelta(days=payload.days)
    current_user.is_premium = True
    await db.commit()
    return {"status": "ok", "premium_until": current_user.premium_until}


from fastapi import APIRouter

router = APIRouter()

from app.api.admin_payments import router as admin_payments_router  # noqa: E402
from app.api.admin_payments_transactions_cursor import (  # noqa: E402
    router as admin_payments_transactions_cursor_router,
)
from app.api.payments import router as payments_router  # noqa: E402

router.include_router(payments_router)
router.include_router(admin_payments_router)
router.include_router(admin_payments_transactions_cursor_router)
