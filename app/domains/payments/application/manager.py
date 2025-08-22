from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.payments.manager_impl import load_active_gateways as _load_active_gateways
from app.domains.payments.manager_impl import verify_payment as _verify_payment


async def load_active_gateways(db: AsyncSession):
    """Возвращает активные гейтвеи (инфраструктурная реализация скрыта)."""
    return await _load_active_gateways(db)


async def verify_payment(
    db: AsyncSession,
    *,
    amount: int,
    currency: str | None,
    token: str,
    preferred_slug: str | None = None,
) -> Tuple[bool, Optional[str]]:
    """Фасад верификации платежа. Делегирует текущей реализации."""
    return await _verify_payment(
        db,
        amount=amount,
        currency=currency,
        token=token,
        preferred_slug=preferred_slug,
    )
