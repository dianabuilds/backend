from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.payments.infrastructure.repositories.ledger_repository import LedgerRepository


class LedgerService:
    def __init__(self, repo: LedgerRepository | None = None) -> None:
        self._repo = repo or LedgerRepository()

    async def capture(
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
        return await self._repo.capture_transaction(
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
