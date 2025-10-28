from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.metrics import (
    set_contract_inventory,
    set_network_metrics,
    set_subscription_metrics,
)
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
        self._amount_column: str | None = None
        self._plan_interval_column: str | None = None

    async def kpi(self) -> JsonDict:
        ok = err = pending = 0
        vol = 0
        avg_confirm_ms = 0.0
        contract_stats: dict[str, int] = {}
        try:
            async with self._engine.begin() as conn:
                amount_column = await self._resolve_payment_amount_column(conn)
                coalesced_amount = f"coalesce({amount_column}, 0)"
                q = await conn.execute(
                    text(
                        f"""
                        WITH tx AS (
                            SELECT
                                count(*) FILTER (WHERE status in ('captured','succeeded','success','completed')) AS success,
                                count(*) FILTER (WHERE status in ('failed','error','declined')) AS failed,
                                count(*) FILTER (WHERE status in ('pending','processing')) AS pending,
                                coalesce(
                                    sum(
                                        CASE
                                            WHEN status in ('captured','succeeded','success','completed')
                                                THEN {coalesced_amount}
                                            ELSE 0
                                        END
                                    ),
                                    0
                                ) AS volume_cents,
                                avg(extract(epoch from (coalesce(confirmed_at, created_at) - created_at)) * 1000.0) FILTER (WHERE confirmed_at IS NOT NULL) AS avg_ms
                            FROM payment_transactions
                        ),
                        contracts AS (
                            SELECT
                                count(*) AS total,
                                count(*) FILTER (WHERE enabled) AS enabled,
                                count(*) FILTER (WHERE NOT enabled) AS disabled,
                                count(*) FILTER (WHERE testnet) AS testnet,
                                count(*) FILTER (WHERE NOT testnet) AS mainnet
                            FROM payment_contracts
                        )
                        SELECT
                            tx.success,
                            tx.failed,
                            tx.pending,
                            tx.volume_cents,
                            tx.avg_ms,
                            contracts.total,
                            contracts.enabled,
                            contracts.disabled,
                            contracts.testnet,
                            contracts.mainnet
                        FROM tx, contracts
                        """
                    )
                )
                row = q.mappings().first() or {}
                ok = int(row.get("success") or 0)
                err = int(row.get("failed") or 0)
                pending = int(row.get("pending") or 0)
                vol = int(row.get("volume_cents") or 0)
                avg_confirm_ms = float(row.get("avg_ms") or 0.0)
                contract_stats = {
                    "total": int(row.get("total") or 0),
                    "enabled": int(row.get("enabled") or 0),
                    "disabled": int(row.get("disabled") or 0),
                    "testnet": int(row.get("testnet") or 0),
                    "mainnet": int(row.get("mainnet") or 0),
                }
        except SQLAlchemyError as exc:
            logger.warning(
                "Failed to compute billing KPI totals: %s", exc, exc_info=exc
            )
            contract_stats = {}
        else:
            if contract_stats:
                set_contract_inventory(contract_stats)
        return {
            "success": ok,
            "errors": err,
            "pending": pending,
            "volume_cents": vol,
            "avg_confirm_ms": avg_confirm_ms,
            "contracts": contract_stats,
        }

    async def subscription_metrics(self) -> JsonDict:
        active_subs = 0
        mrr = 0.0
        arpu = 0.0
        churn_30d = 0.0
        token_rows: list[dict[str, object]] = []
        network_rows: list[dict[str, object]] = []
        try:
            async with self._engine.begin() as conn:
                subs = await conn.execute(
                    text(
                        "SELECT count(*) AS n FROM user_subscriptions WHERE status='active'"
                    )
                )
                active_subs = int((subs.mappings().first() or {}).get("n", 0))
                interval_expression = await self._plan_interval_expression(conn)
                revenue = await conn.execute(
                    text(
                        f"""
                        SELECT coalesce(
                            sum(
                                CASE
                                    WHEN {interval_expression} = 'year'
                                        THEN coalesce(sp.price_cents, 0) / 12.0
                                    ELSE coalesce(sp.price_cents, 0)
                                END
                            ),
                            0
                        ) AS cents
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
                token_cursor = await conn.execute(
                    text(
                        f"""
                        SELECT
                            coalesce(nullif(sp.price_token, ''), coalesce(sp.currency, 'USD')) AS token,
                            count(*) AS total,
                            coalesce(
                                sum(
                                    CASE
                                        WHEN {interval_expression} = 'year'
                                            THEN coalesce(sp.price_cents, 0) / 12.0
                                        ELSE coalesce(sp.price_cents, 0)
                                    END
                                ),
                                0
                            ) AS cents
                        FROM user_subscriptions us
                        JOIN subscription_plans sp ON sp.id = us.plan_id
                        WHERE us.status = 'active'
                        GROUP BY token
                        ORDER BY total DESC
                        """
                    )
                )
                token_rows = [
                    {
                        "token": row["token"] or "USD",
                        "total": int(row["total"] or 0),
                        "mrr_usd": float(row["cents"] or 0.0) / 100.0,
                    }
                    for row in token_cursor.mappings().all()
                ]
                network_cursor = await conn.execute(
                    text(
                        """
                        SELECT
                            coalesce(pc.chain, 'unknown') AS network,
                            coalesce(pc.chain_id::text, 'unknown') AS chain_id,
                            count(*) AS total
                        FROM user_subscriptions us
                        JOIN subscription_plans sp ON sp.id = us.plan_id
                        LEFT JOIN LATERAL (
                            SELECT chain, chain_id
                            FROM payment_contracts pc_inner
                            WHERE pc_inner.slug = sp.contract_slug
                               OR pc_inner.id::text = sp.contract_slug
                            LIMIT 1
                        ) pc ON TRUE
                        WHERE us.status = 'active'
                        GROUP BY network, chain_id
                        ORDER BY total DESC
                        """
                    )
                )
                network_rows = [
                    {
                        "network": row["network"],
                        "chain_id": row["chain_id"],
                        "total": int(row["total"] or 0),
                    }
                    for row in network_cursor.mappings().all()
                ]
        except SQLAlchemyError as exc:
            logger.warning("Failed to compute billing metrics: %s", exc, exc_info=exc)
            token_rows = []
            network_rows = []
        else:
            set_subscription_metrics(
                active=active_subs,
                mrr=mrr,
                arpu=arpu,
                churn_ratio=churn_30d,
                per_token=token_rows,
                per_network=network_rows,
            )
        return {
            "active_subs": active_subs,
            "mrr": mrr,
            "arpu": arpu,
            "churn_30d": churn_30d,
            "tokens": token_rows,
            "networks": network_rows,
        }

    async def revenue_timeseries(self, days: int = 30) -> JsonDictList:
        safe_days = int(max(1, min(days, 365)))
        try:
            async with self._engine.begin() as conn:
                amount_column = await self._resolve_payment_amount_column(conn)
                res = await conn.execute(
                    text(
                        f"""
                        SELECT date_trunc('day', created_at) AS day, coalesce(sum({amount_column}), 0) AS cents
                        FROM payment_transactions
                        WHERE status in ('captured','succeeded','success')
                          AND created_at >= now() - (:days * interval '1 day')
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

    async def network_breakdown(self) -> JsonDictList:
        try:
            async with self._engine.begin() as conn:
                amount_column = await self._resolve_payment_amount_column(conn)
                res = await conn.execute(
                    text(
                        f"""
                        SELECT
                            coalesce(network, 'unknown') AS network,
                            coalesce(token, 'N/A') AS token,
                            count(*) AS total,
                            sum(CASE WHEN status in ('captured','succeeded','success','completed') THEN 1 ELSE 0 END) AS succeeded,
                            sum(CASE WHEN status in ('failed','error','declined') THEN 1 ELSE 0 END) AS failed,
                            sum(CASE WHEN status in ('pending','processing') THEN 1 ELSE 0 END) AS pending,
                            coalesce(sum({amount_column}), 0) AS gross_cents
                        FROM payment_transactions
                        GROUP BY network, token
                        ORDER BY total DESC
                        """
                    )
                )
                rows = res.mappings().all()
        except SQLAlchemyError as exc:
            logger.warning("Failed to compute network breakdown: %s", exc, exc_info=exc)
            return []
        data = [
            {
                "network": r["network"],
                "token": r["token"],
                "total": int(r["total"] or 0),
                "succeeded": int(r["succeeded"] or 0),
                "failed": int(r["failed"] or 0),
                "pending": int(r["pending"] or 0),
                "volume": float(r["gross_cents"] or 0) / 100.0,
            }
            for r in rows
        ]
        set_network_metrics(data)
        return data

    async def _column_exists(self, conn, table_name: str, column_name: str) -> bool:
        result = await conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = ANY (current_schemas(false))
                  AND table_name = :table_name
                  AND column_name = :column_name
                LIMIT 1
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        )
        return result.scalar() is not None

    async def _resolve_payment_amount_column(self, conn) -> str:
        if self._amount_column:
            return self._amount_column
        for candidate in ("gross_cents", "amount_cents", "net_cents"):
            if await self._column_exists(conn, "payment_transactions", candidate):
                self._amount_column = candidate
                break
        if not self._amount_column:
            self._amount_column = "net_cents"
            logger.warning(
                "payment_transactions lacks {gross,amount,net}_cents columns; falling back to net_cents"
            )
        return self._amount_column

    async def _plan_interval_expression(self, conn) -> str:
        if self._plan_interval_column is None:
            has_column = await self._column_exists(
                conn, "subscription_plans", "billing_interval"
            )
            self._plan_interval_column = "billing_interval" if has_column else ""
            if not has_column:
                logger.warning(
                    "subscription_plans.billing_interval is missing; defaulting to 'month'"
                )
        if self._plan_interval_column:
            return f"coalesce(sp.{self._plan_interval_column}, 'month')"
        return "'month'"


__all__ = ["SQLBillingAnalyticsRepo"]
