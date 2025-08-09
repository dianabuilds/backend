from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PremiumPurchaseIn
from app.services.payments import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/premium", response_model=dict)
async def buy_premium(
    payload: PremiumPurchaseIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    amount = payload.days  # 1 token per day in this simplified example
    if not await payment_service.verify(payload.payment_token, amount):
        raise HTTPException(status_code=400, detail="Payment not confirmed")

    now = datetime.utcnow()
    if current_user.premium_until and current_user.premium_until > now:
        current_user.premium_until += timedelta(days=payload.days)
    else:
        current_user.premium_until = now + timedelta(days=payload.days)
    current_user.is_premium = True
    await db.commit()
    return {"status": "ok", "premium_until": current_user.premium_until}
