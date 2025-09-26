from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.domain.models import Plan, Subscription
from domains.platform.billing.ports import (
    GatewayRepo,
    LedgerRepo,
    PlanRepo,
    SubscriptionRepo,
)
from packages.core.db import get_async_engine


class SQLPlanRepo(PlanRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine) if isinstance(engine, str) else engine
        )

    async def list_active(self) -> list[Plan]:
        sql = text(
            "SELECT id, slug, title, description, price_cents, currency, is_active, order, monthly_limits, features, created_at, updated_at FROM subscription_plans WHERE is_active = true ORDER BY order, created_at"
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql)
            rows = res.mappings().all()
            return [
                Plan(
                    id=str(r["id"]),
                    slug=str(r["slug"]),
                    title=str(r["title"]),
                    price_cents=(int(r["price_cents"]) if r["price_cents"] is not None else None),
                    currency=(str(r["currency"]) if r["currency"] else None),
                    is_active=bool(r["is_active"]),
                    order=int(r["order"]),
                    monthly_limits=(
                        dict(r["monthly_limits"]) if r["monthly_limits"] is not None else None
                    ),
                    features=(dict(r["features"]) if r["features"] is not None else None),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    async def list_all(self) -> list[Plan]:
        sql = text(
            "SELECT id, slug, title, description, price_cents, currency, is_active, order, monthly_limits, features, created_at, updated_at FROM subscription_plans ORDER BY order, created_at"
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql)
            rows = res.mappings().all()
            return [
                Plan(
                    id=str(r["id"]),
                    slug=str(r["slug"]),
                    title=str(r["title"]),
                    price_cents=(int(r["price_cents"]) if r["price_cents"] is not None else None),
                    currency=(str(r["currency"]) if r["currency"] else None),
                    is_active=bool(r["is_active"]),
                    order=int(r["order"]),
                    monthly_limits=(
                        dict(r["monthly_limits"]) if r["monthly_limits"] is not None else None
                    ),
                    features=(dict(r["features"]) if r["features"] is not None else None),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    async def get_by_slug(self, slug: str) -> Plan | None:
        sql = text(
            "SELECT id, slug, title, description, price_cents, currency, is_active, order, monthly_limits, features, created_at, updated_at FROM subscription_plans WHERE slug = :slug"
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, {"slug": slug})
            r = res.mappings().first()
            if not r:
                return None
            return Plan(
                id=str(r["id"]),
                slug=str(r["slug"]),
                title=str(r["title"]),
                price_cents=(int(r["price_cents"]) if r["price_cents"] is not None else None),
                currency=(str(r["currency"]) if r["currency"] else None),
                is_active=bool(r["is_active"]),
                order=int(r["order"]),
                monthly_limits=(
                    dict(r["monthly_limits"]) if r["monthly_limits"] is not None else None
                ),
                features=(dict(r["features"]) if r["features"] is not None else None),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    async def get_by_id(self, plan_id: str) -> Plan | None:
        sql = text(
            "SELECT id, slug, title, description, price_cents, currency, is_active, order, monthly_limits, features, created_at, updated_at FROM subscription_plans WHERE id = cast(:id as uuid)"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": plan_id})).mappings().first()
            if not r:
                return None
            return Plan(
                id=str(r["id"]),
                slug=str(r["slug"]),
                title=str(r["title"]),
                price_cents=(int(r["price_cents"]) if r["price_cents"] is not None else None),
                currency=(str(r["currency"]) if r["currency"] else None),
                is_active=bool(r["is_active"]),
                order=int(r["order"]),
                monthly_limits=(
                    dict(r["monthly_limits"]) if r["monthly_limits"] is not None else None
                ),
                features=(dict(r["features"]) if r["features"] is not None else None),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    async def upsert(self, p: dict[str, Any]) -> Plan:
        sql = text(
            """
            INSERT INTO subscription_plans (id, slug, title, description, price_cents, currency, is_active, "order", monthly_limits, features, created_at, updated_at)
            VALUES (coalesce(:id, gen_random_uuid()), :slug, :title, :description, :price_cents, :currency, coalesce(:is_active,true), coalesce(:order,100), cast(:monthly_limits as jsonb), cast(:features as jsonb), now(), now())
            ON CONFLICT (slug) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                price_cents = excluded.price_cents,
                currency = excluded.currency,
                is_active = excluded.is_active,
                "order" = excluded."order",
                monthly_limits = excluded.monthly_limits,
                features = excluded.features,
                updated_at = now()
            RETURNING id, slug, title, description, price_cents, currency, is_active, "order", monthly_limits, features, created_at, updated_at
            """
        )
        payload = {
            "id": p.get("id"),
            "slug": p["slug"],
            "title": p["title"],
            "description": p.get("description"),
            "price_cents": p.get("price_cents"),
            "currency": p.get("currency"),
            "is_active": p.get("is_active", True),
            "order": p.get("order", 100),
            "monthly_limits": p.get("monthly_limits"),
            "features": p.get("features"),
        }
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, payload)
            r = res.mappings().first()
            assert r is not None
            return Plan(
                id=str(r["id"]),
                slug=str(r["slug"]),
                title=str(r["title"]),
                price_cents=(int(r["price_cents"]) if r["price_cents"] is not None else None),
                currency=(str(r["currency"]) if r["currency"] else None),
                is_active=bool(r["is_active"]),
                order=int(r["order"]),
                monthly_limits=(
                    dict(r["monthly_limits"]) if r["monthly_limits"] is not None else None
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
            get_async_engine("billing", url=engine) if isinstance(engine, str) else engine
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
        self, user_id: str, plan_id: str, auto_renew: bool, ends_at: str | None = None
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
            assert r is not None
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
            get_async_engine("billing", url=engine) if isinstance(engine, str) else engine
        )

    async def add_tx(self, tx: dict[str, Any]) -> None:
        sql = text(
            """
            INSERT INTO payment_transactions(id, user_id, gateway_slug, product_type, product_id, currency, gross_cents, fee_cents, net_cents, status, created_at, meta)
            VALUES (gen_random_uuid(), :user_id, :gateway_slug, :product_type, :product_id, :currency, :gross_cents, :fee_cents, :net_cents, :status, now(), cast(:meta as jsonb))
            """
        )
        async with self._engine.begin() as conn:
            await conn.execute(sql, tx)

    async def list_for_user(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, user_id, gateway_slug, currency, gross_cents, fee_cents, net_cents, status, created_at, meta
            FROM payment_transactions
            WHERE user_id = cast(:uid as uuid)
            ORDER BY created_at DESC
            LIMIT :lim
            """
        )
        try:
            async with self._engine.begin() as conn:
                rows = (
                    (await conn.execute(sql, {"uid": user_id, "lim": int(max(1, min(limit, 100)))}))
                    .mappings()
                    .all()
                )
                return [dict(r) for r in rows]
        except Exception:
            raise

    async def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        try:
            sql = text(
                """
                SELECT id, user_id, gateway_slug, currency, gross_cents, fee_cents, net_cents, status, created_at, meta
                FROM payment_transactions
                ORDER BY created_at DESC
                LIMIT :lim
                """
            )
            async with self._engine.begin() as conn:
                rows = (
                    (await conn.execute(sql, {"lim": int(max(1, min(limit, 1000)))}))
                    .mappings()
                    .all()
                )
                return [dict(r) for r in rows]
        except Exception:
            # Table may be absent or schema incompatible; return empty for admin list
            return []


class SQLGatewaysRepo(GatewayRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("billing", url=engine) if isinstance(engine, str) else engine
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
            assert r is not None
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
