from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.ports import BillingHistory, BillingHistoryRepo
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


class SQLBillingHistoryRepo(BillingHistoryRepo):
    """SQL adapter that exposes user transaction history."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def get_history(self, user_id: str, limit: int = 20) -> BillingHistory:
        safe_limit = int(max(1, min(limit, 100)))
        query = text(
            """
            SELECT id,
                   gateway_slug,
                   currency,
                   gross_cents,
                   status,
                   created_at,
                   product_type,
                   meta
            FROM payment_transactions
            WHERE user_id = cast(:uid AS uuid)
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        try:
            async with self._engine.begin() as conn:
                rows = (
                    (await conn.execute(query, {"uid": user_id, "lim": safe_limit}))
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to load billing history for user %s: %s",
                user_id,
                exc,
                exc_info=exc,
            )
            return BillingHistory(items=[], coming_soon=True)

        items = []
        for row in rows:
            gross = row.get("gross_cents")
            amount = _to_amount(gross)
            meta = row.get("meta") or {}
            if not isinstance(meta, dict):
                try:
                    meta = dict(meta)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    meta = {}
            items.append(
                {
                    "id": _to_str(row.get("id")),
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                    "amount": amount,
                    "currency": row.get("currency"),
                    "provider": row.get("gateway_slug"),
                    "product_type": row.get("product_type"),
                    "meta": meta,
                }
            )
        return BillingHistory(items=items, coming_soon=False)


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_amount(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        cents = float(value)
    elif isinstance(value, (int, float)):
        cents = float(value)
    else:
        try:
            cents = float(value)
        except (TypeError, ValueError):
            return None
    return cents / 100.0


__all__ = ["SQLBillingHistoryRepo"]
