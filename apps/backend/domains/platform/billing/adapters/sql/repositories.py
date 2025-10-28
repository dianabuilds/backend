from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.domain.models import Plan, Subscription
from domains.platform.billing.ports import (
    GatewayRepo,
    LedgerRepo,
    PlanRepo,
    SubscriptionRepo,
)
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


class SQLPlanRepo(PlanRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    @staticmethod
    def _row_to_plan(row: Any) -> Plan:
        price_cents = (
            int(row["price_cents"]) if row.get("price_cents") is not None else None
        )
        usd_estimate = row.get("price_usd_estimate")
        if isinstance(usd_estimate, Decimal):
            usd_estimate_val: float | None = float(usd_estimate)
        elif usd_estimate is None:
            usd_estimate_val = None
        else:
            try:
                usd_estimate_val = float(usd_estimate)
            except (TypeError, ValueError):
                usd_estimate_val = None

        monthly_limits = row.get("monthly_limits")
        if monthly_limits is not None and not isinstance(monthly_limits, dict):
            try:
                monthly_limits = dict(monthly_limits)
            except (TypeError, ValueError):
                monthly_limits = None

        features = row.get("features")
        if features is not None and not isinstance(features, dict):
            try:
                features = dict(features)
            except (TypeError, ValueError):
                features = None

        price_token = row.get("price_token")
        if price_token:
            price_token = str(price_token)

        gateway_slug = row.get("gateway_slug")
        if gateway_slug:
            gateway_slug = str(gateway_slug)

        contract_slug = row.get("contract_slug")
        if contract_slug:
            contract_slug = str(contract_slug)

        return Plan(
            id=str(row["id"]),
            slug=str(row["slug"]),
            title=str(row["title"]),
            price_cents=price_cents,
            price_token=price_token,
            price_usd_estimate=usd_estimate_val,
            billing_interval=str(row.get("billing_interval") or "month"),
            gateway_slug=gateway_slug,
            contract_slug=contract_slug,
            currency=(str(row["currency"]) if row.get("currency") else None),
            is_active=bool(row["is_active"]),
            order=int(row["order"]),
            monthly_limits=monthly_limits,
            features=features,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_active(self) -> list[Plan]:
        sql = text(
            """
            SELECT id,
                   slug,
                   title,
                   description,
                   price_cents,
                   price_token,
                   price_usd_estimate,
                   billing_interval,
                   gateway_slug,
                   contract_slug,
                   currency,
                   is_active,
                   "order",
                   monthly_limits,
                   features,
                   created_at,
                   updated_at
            FROM subscription_plans
            WHERE is_active = true
            ORDER BY "order", created_at
            """
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql)
            rows = res.mappings().all()
            return [self._row_to_plan(r) for r in rows]

    async def list_all(self) -> list[Plan]:
        sql = text(
            """
            SELECT id,
                   slug,
                   title,
                   description,
                   price_cents,
                   price_token,
                   price_usd_estimate,
                   billing_interval,
                   gateway_slug,
                   contract_slug,
                   currency,
                   is_active,
                   "order",
                   monthly_limits,
                   features,
                   created_at,
                   updated_at
            FROM subscription_plans
            ORDER BY "order", created_at
            """
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql)
            rows = res.mappings().all()
            return [self._row_to_plan(r) for r in rows]

    async def get_by_slug(self, slug: str) -> Plan | None:
        sql = text(
            """
            SELECT id,
                   slug,
                   title,
                   description,
                   price_cents,
                   price_token,
                   price_usd_estimate,
                   billing_interval,
                   gateway_slug,
                   contract_slug,
                   currency,
                   is_active,
                   "order",
                   monthly_limits,
                   features,
                   created_at,
                   updated_at
            FROM subscription_plans
            WHERE slug = :slug
            """
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, {"slug": slug})
            r = res.mappings().first()
            if not r:
                return None
            return self._row_to_plan(r)

    async def get_by_id(self, plan_id: str) -> Plan | None:
        sql = text(
            """
            SELECT id,
                   slug,
                   title,
                   description,
                   price_cents,
                   price_token,
                   price_usd_estimate,
                   billing_interval,
                   gateway_slug,
                   contract_slug,
                   currency,
                   is_active,
                   "order",
                   monthly_limits,
                   features,
                   created_at,
                   updated_at
            FROM subscription_plans
            WHERE id = cast(:id as uuid)
            """
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": plan_id})).mappings().first()
            if not r:
                return None
            return self._row_to_plan(r)

    async def upsert(self, p: dict[str, Any]) -> Plan:
        sql = text(
            """
            INSERT INTO subscription_plans (
                id,
                slug,
                title,
                description,
                price_cents,
                price_token,
                price_usd_estimate,
                billing_interval,
                gateway_slug,
                contract_slug,
                currency,
                is_active,
                "order",
                monthly_limits,
                features,
                created_at,
                updated_at
            )
            VALUES (
                coalesce(:id, gen_random_uuid()),
                :slug,
                :title,
                :description,
                :price_cents,
                :price_token,
                :price_usd_estimate,
                coalesce(:billing_interval,'month'),
                :gateway_slug,
                :contract_slug,
                :currency,
                coalesce(:is_active,true),
                coalesce(:order,100),
                cast(:monthly_limits as jsonb),
                cast(:features as jsonb),
                now(),
                now()
            )
            ON CONFLICT (slug) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                price_cents = excluded.price_cents,
                price_token = excluded.price_token,
                price_usd_estimate = excluded.price_usd_estimate,
                billing_interval = excluded.billing_interval,
                gateway_slug = excluded.gateway_slug,
                contract_slug = excluded.contract_slug,
                currency = excluded.currency,
                is_active = excluded.is_active,
                "order" = excluded."order",
                monthly_limits = excluded.monthly_limits,
                features = excluded.features,
                updated_at = now()
            RETURNING id,
                      slug,
                      title,
                      description,
                      price_cents,
                      price_token,
                      price_usd_estimate,
                      billing_interval,
                      gateway_slug,
                      contract_slug,
                      currency,
                      is_active,
                      "order",
                      monthly_limits,
                      features,
                      created_at,
                      updated_at
            """
        )
        payload = {
            "id": p.get("id"),
            "slug": p["slug"],
            "title": p["title"],
            "description": p.get("description"),
            "price_cents": p.get("price_cents"),
            "price_token": p.get("price_token"),
            "price_usd_estimate": p.get("price_usd_estimate"),
            "billing_interval": p.get("billing_interval"),
            "gateway_slug": p.get("gateway_slug"),
            "contract_slug": p.get("contract_slug"),
            "currency": p.get("currency"),
            "is_active": p.get("is_active", True),
            "order": p.get("order", 100),
            "monthly_limits": p.get("monthly_limits"),
            "features": p.get("features"),
        }
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, payload)
            r = res.mappings().first()
            if r is None:

                raise RuntimeError("database_row_missing")
            return Plan(
                id=str(r["id"]),
                slug=str(r["slug"]),
                title=str(r["title"]),
                price_cents=(
                    int(r["price_cents"]) if r["price_cents"] is not None else None
                ),
                currency=(str(r["currency"]) if r["currency"] else None),
                is_active=bool(r["is_active"]),
                order=int(r["order"]),
                monthly_limits=(
                    dict(r["monthly_limits"])
                    if r["monthly_limits"] is not None
                    else None
                ),
                features=(dict(r["features"]) if r["features"] is not None else None),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    async def delete(self, plan_id: str) -> None:
        sql = text("DELETE FROM subscription_plans WHERE id = :id")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": plan_id})


class SQLSubscriptionRepo(SubscriptionRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def get_active_for_user(self, user_id: str) -> Subscription | None:
        sql = text(
            "SELECT * FROM user_subscriptions WHERE user_id=:uid AND status='active' ORDER BY created_at DESC LIMIT 1"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"uid": user_id})).mappings().first()
            if not r:
                return None
            return Subscription(
                id=str(r["id"]),
                user_id=str(r["user_id"]),
                plan_id=str(r["plan_id"]),
                status=str(r["status"]),
                auto_renew=bool(r["auto_renew"]),
                started_at=r["started_at"],
                ends_at=r["ends_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    async def activate(
        self,
        user_id: str,
        plan_id: str,
        auto_renew: bool = True,
        ends_at: str | None = None,
    ) -> Subscription:
        sql = text(
            """
            INSERT INTO user_subscriptions (user_id, plan_id, status, auto_renew, started_at, ends_at, created_at, updated_at)
            VALUES (:uid, :pid, 'active', :auto, now(), :ends, now(), now())
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            r = (
                (
                    await conn.execute(
                        sql,
                        {
                            "uid": user_id,
                            "pid": plan_id,
                            "auto": bool(auto_renew),
                            "ends": ends_at,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if r is None:

                raise RuntimeError("database_row_missing")
            return Subscription(
                id=str(r["id"]),
                user_id=str(r["user_id"]),
                plan_id=str(r["plan_id"]),
                status=str(r["status"]),
                auto_renew=bool(r["auto_renew"]),
                started_at=r["started_at"],
                ends_at=r["ends_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )


class SQLLedgerRepo(LedgerRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    @staticmethod
    def _row_to_tx(row: Any) -> dict[str, Any]:
        item = {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "gateway_slug": row.get("gateway_slug"),
            "product_type": row.get("product_type"),
            "product_id": str(row["product_id"]) if row.get("product_id") else None,
            "currency": row.get("currency"),
            "token": row.get("token"),
            "network": row.get("network"),
            "gross_cents": int(row.get("gross_cents") or 0),
            "fee_cents": int(row.get("fee_cents") or 0),
            "net_cents": int(row.get("net_cents") or 0),
            "tx_hash": row.get("tx_hash"),
            "status": row.get("status"),
            "created_at": row.get("created_at"),
            "confirmed_at": row.get("confirmed_at"),
            "failure_reason": row.get("failure_reason"),
            "meta": dict(row["meta"]) if row.get("meta") is not None else None,
        }
        return item

    async def add_tx(self, tx: dict[str, Any]) -> None:
        sql = text(
            """
            INSERT INTO payment_transactions(
                id,
                user_id,
                gateway_slug,
                product_type,
                product_id,
                currency,
                token,
                network,
                gross_cents,
                fee_cents,
                net_cents,
                tx_hash,
                status,
                created_at,
                confirmed_at,
                failure_reason,
                meta
            )
            VALUES (
                gen_random_uuid(),
                :user_id,
                :gateway_slug,
                :product_type,
                :product_id,
                :currency,
                :token,
                :network,
                :gross_cents,
                :fee_cents,
                :net_cents,
                :tx_hash,
                :status,
                coalesce(:created_at, now()),
                :confirmed_at,
                :failure_reason,
                cast(:meta as jsonb)
            )
            """
        )
        payload = {
            "user_id": tx.get("user_id"),
            "gateway_slug": tx.get("gateway_slug"),
            "product_type": tx.get("product_type"),
            "product_id": tx.get("product_id"),
            "currency": tx.get("currency"),
            "token": tx.get("token"),
            "network": tx.get("network"),
            "gross_cents": tx.get("gross_cents"),
            "fee_cents": tx.get("fee_cents"),
            "net_cents": tx.get("net_cents"),
            "tx_hash": tx.get("tx_hash"),
            "status": tx.get("status", "captured"),
            "created_at": tx.get("created_at"),
            "confirmed_at": tx.get("confirmed_at"),
            "failure_reason": tx.get("failure_reason"),
            "meta": tx.get("meta"),
        }
        async with self._engine.begin() as conn:
            await conn.execute(sql, payload)

    async def list_for_user(
        self, user_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT
                id,
                user_id,
                gateway_slug,
                product_type,
                product_id,
                currency,
                token,
                network,
                gross_cents,
                fee_cents,
                net_cents,
                tx_hash,
                status,
                created_at,
                confirmed_at,
                failure_reason,
                meta
            FROM payment_transactions
            WHERE user_id = cast(:uid as uuid)
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        try:
            async with self._engine.begin() as conn:
                rows = (
                    (
                        await conn.execute(
                            sql, {"uid": user_id, "lim": int(max(1, min(limit, 100)))}
                        )
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            logger.error(
                "Failed to list ledger transactions for user %s: %s", user_id, exc
            )
            raise
        return [self._row_to_tx(r) for r in rows]

    async def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT
                id,
                user_id,
                gateway_slug,
                product_type,
                product_id,
                currency,
                token,
                network,
                gross_cents,
                fee_cents,
                net_cents,
                tx_hash,
                status,
                created_at,
                confirmed_at,
                failure_reason,
                meta
            FROM payment_transactions
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        try:
            async with self._engine.begin() as conn:
                rows = (
                    (await conn.execute(sql, {"lim": int(max(1, min(limit, 1000)))}))
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            logger.warning("Failed to list recent ledger transactions: %s", exc)
            return []
        return [self._row_to_tx(r) for r in rows]

    async def get_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT id, user_id, gateway_slug, product_type, product_id, currency,
                   token, network, gross_cents, fee_cents, net_cents, tx_hash,
                   status, created_at, confirmed_at, failure_reason, meta
            FROM payment_transactions
            WHERE meta ->> 'checkout_external_id' = :external_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (await conn.execute(sql, {"external_id": external_id}))
                .mappings()
                .first()
            )
        return None if row is None else self._row_to_tx(row)

    async def get_by_tx_hash(self, tx_hash: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT id, user_id, gateway_slug, product_type, product_id, currency,
                   token, network, gross_cents, fee_cents, net_cents, tx_hash,
                   status, created_at, confirmed_at, failure_reason, meta
            FROM payment_transactions
            WHERE tx_hash = :tx_hash
            LIMIT 1
            """
        )
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"tx_hash": tx_hash})).mappings().first()
        return None if row is None else self._row_to_tx(row)

    async def update_transaction(
        self,
        transaction_id: str,
        *,
        status: str,
        tx_hash: str | None = None,
        network: str | None = None,
        token: str | None = None,
        confirmed_at: Any | None = None,
        failure_reason: str | None = None,
        meta_patch: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sql = text(
            """
            UPDATE payment_transactions
            SET
                status = :status,
                tx_hash = COALESCE(:tx_hash, tx_hash),
                network = COALESCE(:network, network),
                token = COALESCE(:token, token),
                confirmed_at = COALESCE(:confirmed_at, confirmed_at),
                failure_reason = :failure_reason,
                meta = CASE
                    WHEN :meta_patch IS NULL THEN meta
                    ELSE coalesce(meta, '{}'::jsonb) || cast(:meta_patch as jsonb)
                END
            WHERE id = :id
            RETURNING id, user_id, gateway_slug, product_type, product_id, currency,
                      token, network, gross_cents, fee_cents, net_cents, tx_hash,
                      status, created_at, confirmed_at, failure_reason, meta
            """
        )
        payload = {
            "id": transaction_id,
            "status": status,
            "tx_hash": tx_hash,
            "network": network,
            "token": token,
            "confirmed_at": confirmed_at,
            "failure_reason": failure_reason,
            "meta_patch": meta_patch,
        }
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, payload)).mappings().first()
        if row is None:
            raise RuntimeError("ledger_transaction_missing")
        return self._row_to_tx(row)

    async def list_pending(
        self, *, older_than_seconds: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, user_id, gateway_slug, product_type, product_id, currency,
                   token, network, gross_cents, fee_cents, net_cents, tx_hash,
                   status, created_at, confirmed_at, failure_reason, meta
            FROM payment_transactions
            WHERE status IN ('pending', 'processing')
              AND (
                :older <= 0
                OR created_at <= now() - (:older * interval '1 second')
              )
            ORDER BY created_at
            LIMIT :lim
            """
        )
        older = max(int(older_than_seconds), 0)
        async with self._engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        sql, {"older": older, "lim": int(max(1, min(limit, 1000)))}
                    )
                )
                .mappings()
                .all()
            )
        return [self._row_to_tx(row) for row in rows]


class SQLGatewaysRepo(GatewayRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def list(self) -> list[dict[str, Any]]:
        sql = text(
            "SELECT slug, type, enabled, priority, config, created_at, updated_at FROM payment_gateways ORDER BY priority, created_at"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql)).mappings().all()
            out: list[dict[str, Any]] = []
            for r in rows:
                item = {
                    "slug": str(r["slug"]),
                    "type": str(r["type"]),
                    "enabled": bool(r["enabled"]),
                    "priority": int(r["priority"]),
                    "config": dict(r["config"]) if r["config"] is not None else None,
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                }
                # Redact sensitive fields in config
                cfg = item.get("config") or {}
                if isinstance(cfg, dict):
                    for k in list(cfg.keys()):
                        if "key" in k.lower() or "secret" in k.lower():
                            cfg[k] = "***"
                out.append(item)
            return out

    async def upsert(self, g: dict[str, Any]) -> dict[str, Any]:
        sql = text(
            """
            INSERT INTO payment_gateways (slug, type, enabled, priority, config, created_at, updated_at)
            VALUES (:slug, :type, coalesce(:enabled,true), coalesce(:priority,100), cast(:config as jsonb), now(), now())
            ON CONFLICT (slug) DO UPDATE SET
                type = excluded.type,
                enabled = excluded.enabled,
                priority = excluded.priority,
                config = excluded.config,
                updated_at = now()
            RETURNING slug, type, enabled, priority, config, created_at, updated_at
            """
        )
        payload = {
            "slug": g.get("slug"),
            "type": g.get("type"),
            "enabled": g.get("enabled", True),
            "priority": g.get("priority", 100),
            "config": g.get("config"),
        }
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, payload)).mappings().first()
            if r is None:

                raise RuntimeError("database_row_missing")
            item = {
                "slug": str(r["slug"]),
                "type": str(r["type"]),
                "enabled": bool(r["enabled"]),
                "priority": int(r["priority"]),
                "config": dict(r["config"]) if r["config"] is not None else None,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            # Redact sensitive values in immediate response
            cfg = item.get("config") or {}
            if isinstance(cfg, dict):
                for k in list(cfg.keys()):
                    if "key" in k.lower() or "secret" in k.lower():
                        cfg[k] = "***"
            return item

    async def delete(self, slug: str) -> None:
        sql = text("DELETE FROM payment_gateways WHERE slug = :slug")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"slug": slug})


__all__ = ["SQLPlanRepo", "SQLSubscriptionRepo", "SQLLedgerRepo", "SQLGatewaysRepo"]
