from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.ports import BillingAnalyticsRepo, JsonDict, JsonDictList
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


class SQLBillingAnalyticsRepo(BillingAnalyticsRepo):
    """SQL-backed агрегатор метрик биллинга."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing-analytics", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def kpi(self) -> JsonDict:
        ok = err = vol = 0
        try:
            async with self._engine.begin() as conn:
                success = await conn.execute(
                    text(
                        "SELECT count(*) AS n FROM payment_transactions WHERE status in ('captured','succeeded','success')"
                    )
                )
                errors = await conn.execute(
                    text(
                        "SELECT count(*) AS n FROM payment_transactions WHERE status in ('failed','error','declined')"
                    )
                )
                volume = await conn.execute(
                    text(
                        "SELECT coalesce(sum(gross_cents),0) AS v FROM payment_transactions WHERE status in ('captured','succeeded','success')"
                    )
                )
                ok = int((success.mappings().first() or {}).get("n", 0))
                err = int((errors.mappings().first() or {}).get("n", 0))
                vol = int((volume.mappings().first() or {}).get("v", 0))
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to compute billing KPI totals: %s", exc, exc_info=exc
            )
        avg_confirm_ms = 0.0
        try:
            async with self._engine.begin() as conn:
                r = (
                    (
                        await conn.execute(
                            text(
                                """
                            SELECT avg(extract(epoch from (to_timestamp((meta->>'confirmed_at')::double precision) - created_at))*1000.0) AS ms
                            FROM payment_transactions
                            WHERE (meta ? 'confirmed_at')
                            """
                            )
                        )
                    )
                    .mappings()
                    .first()
                )
                if r and r.get("ms") is not None:
                    avg_confirm_ms = float(r.get("ms") or 0.0)
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to compute confirmation metrics: %s", exc, exc_info=exc
            )
        return {
            "success": ok,
            "errors": err,
            "volume_cents": vol,
            "avg_confirm_ms": avg_confirm_ms,
        }

    async def subscription_metrics(self) -> JsonDict:
        active_subs = 0
        mrr = 0.0
        arpu = 0.0
        churn_30d = 0.0
        try:
            async with self._engine.begin() as conn:
                subs = await conn.execute(
                    text(
                        "SELECT count(*) AS n FROM user_subscriptions WHERE status='active'"
                    )
                )
                active_subs = int((subs.mappings().first() or {}).get("n", 0))
                revenue = await conn.execute(
                    text(
                        """
                        SELECT coalesce(sum(CASE WHEN (sp.features->>'interval') = 'year' THEN (sp.price_cents/12.0) ELSE sp.price_cents END),0) AS cents
                        FROM user_subscriptions us
                        JOIN subscription_plans sp ON sp.id = us.plan_id
                        WHERE us.status='active'
                        """
                    )
                )
                mrr_cents = float((revenue.mappings().first() or {}).get("cents", 0.0))
                mrr = mrr_cents / 100.0
                arpu = mrr / max(active_subs, 1)
                churn = await conn.execute(
                    text(
                        "SELECT count(*) n FROM user_subscriptions WHERE status!='active' AND updated_at >= now() - interval '30 days'"
                    )
                )
                ended = int((churn.mappings().first() or {}).get("n", 0))
                churn_30d = ended / max(active_subs + ended, 1)
        except SQLAlchemyError as exc:
            logger.warning("Failed to compute billing metrics: %s", exc, exc_info=exc)
        return {
            "active_subs": active_subs,
            "mrr": mrr,
            "arpu": arpu,
            "churn_30d": churn_30d,
        }

    async def revenue_timeseries(self, days: int = 30) -> JsonDictList:
        safe_days = int(max(1, min(days, 365)))
        try:
            async with self._engine.begin() as conn:
                res = await conn.execute(
                    text(
                        """
                        SELECT date_trunc('day', created_at) AS day, sum(gross_cents) AS cents
                        FROM payment_transactions
                        WHERE status in ('captured','succeeded','success')
                          AND created_at >= now() - (:days::text || ' days')::interval
                        GROUP BY day
                        ORDER BY day
                        """
                    ),
                    {"days": safe_days},
                )
                rows = res.mappings().all()
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to compute revenue time series: %s", exc, exc_info=exc
            )
            return []
        return [
            {"day": r["day"].isoformat(), "amount": float(r["cents"] or 0.0) / 100.0}
            for r in rows
        ]


__all__ = ["SQLBillingAnalyticsRepo"]
