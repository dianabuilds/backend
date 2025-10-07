from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.ports import BillingSummary, BillingSummaryRepo
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


class SQLBillingSummaryRepo(BillingSummaryRepo):
    """SQL adapter for composing user billing summary."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def get_summary(self, user_id: str) -> BillingSummary:
        query = text(
            """
            SELECT
                us.plan_id            AS subscription_plan_id,
                us.status            AS subscription_status,
                us.auto_renew        AS subscription_auto_renew,
                us.started_at        AS subscription_started_at,
                us.ends_at           AS subscription_ends_at,
                sp.id                AS plan_id,
                sp.slug              AS plan_slug,
                sp.title             AS plan_title,
                sp.price_cents       AS plan_price_cents,
                sp.currency          AS plan_currency,
                sp.features          AS plan_features
            FROM user_subscriptions us
            LEFT JOIN subscription_plans sp ON sp.id = us.plan_id
            WHERE us.user_id = cast(:uid AS uuid)
              AND us.status = 'active'
            ORDER BY us.updated_at DESC
            LIMIT 1
            """
        )
        try:
            async with self._engine.begin() as conn:
                row = (await conn.execute(query, {"uid": user_id})).mappings().first()
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to load billing summary for user %s: %s",
                user_id,
                exc,
                exc_info=exc,
            )
            return BillingSummary(plan=None, subscription=None)
        if not row:
            return BillingSummary(plan=None, subscription=None)

        subscription = None
        if row.get("subscription_status") or row.get("subscription_plan_id"):
            subscription = {
                "plan_id": _to_str(row.get("subscription_plan_id")),
                "status": row.get("subscription_status"),
                "auto_renew": row.get("subscription_auto_renew"),
                "started_at": row.get("subscription_started_at"),
                "ends_at": row.get("subscription_ends_at"),
            }

        plan = None
        if row.get("plan_id"):
            price_cents = _to_int(row.get("plan_price_cents"))
            features = row.get("plan_features") or None
            if features is not None and not isinstance(features, dict):
                try:
                    features = dict(features)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    features = None
            plan = {
                "id": _to_str(row.get("plan_id")),
                "slug": row.get("plan_slug"),
                "title": row.get("plan_title"),
                "price_cents": price_cents,
                "currency": row.get("plan_currency"),
                "features": features,
            }

        return BillingSummary(plan=plan, subscription=subscription)


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


__all__ = ["SQLBillingSummaryRepo"]
