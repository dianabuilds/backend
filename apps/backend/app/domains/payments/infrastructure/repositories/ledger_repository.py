from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.payments.ledger_impl import capture_transaction as _capture_transaction


class LedgerRepository:
    async def capture_transaction(
        self,
        db: AsyncSession,
        *,
        user_id,
        gateway_slug: str | None,
        product_type: str,
        product_id,
        gross_cents: int,
        currency: str | None = "USD",
        status: str = "captured",
        extra_meta: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return await _capture_transaction(
            db,
            user_id=user_id,
            gateway_slug=gateway_slug,
            product_type=product_type,
            product_id=product_id,
            gross_cents=gross_cents,
            currency=currency,
            status=status,
            extra_meta=extra_meta,
        )
