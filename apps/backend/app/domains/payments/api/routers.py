from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.payments.api_admin import router as admin_payments_router
from app.domains.payments.application.payments_service import PaymentService
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.payment import PremiumPurchaseIn

public_router = APIRouter(prefix="/payments", tags=["payments"])


@public_router.post("/premium", response_model=dict, summary="Buy premium")
async def buy_premium(
    payload: PremiumPurchaseIn,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
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


router = APIRouter()
router.include_router(public_router)
router.include_router(admin_payments_router)

__all__ = ["router"]
