from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import require_role
from app.db.session import get_db
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import AdminPaymentOut
from app.services.payments import payment_service

router = APIRouter(prefix="/admin/payments", tags=["admin"])


@router.get("", response_model=list[AdminPaymentOut], summary="List payments")
async def list_payments(
    status: str | None = None,
    source: str | None = None,
    user_id: UUID | None = None,
    page: int = 1,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payment).order_by(Payment.created_at.desc())
    if status:
        stmt = stmt.where(Payment.status == status)
    if source:
        stmt = stmt.where(Payment.source == source)
    if user_id:
        stmt = stmt.where(Payment.user_id == user_id)
    limit = 50
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{payment_id}", summary="Get payment payload")
async def get_payment_payload(
    payment_id: UUID,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment.payload or {}


@router.post("/{payment_id}/reverify", summary="Reverify payment")
async def reverify_payment(
    payment_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    token = None
    if isinstance(payment.payload, dict):
        token = payment.payload.get("payment_token")
    if not token:
        raise HTTPException(status_code=400, detail="No token to verify")
    verified = await payment_service.verify(token, payment.days)
    payment.status = "confirmed" if verified else "failed"
    await db.commit()
    return {"status": payment.status}
