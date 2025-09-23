from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.billing.ports import ContractsRepo


def _normalize_async_dsn(url: str) -> str:
    out = url
    if out.startswith("postgresql://"):
        out = "postgresql+asyncpg://" + out[len("postgresql://") :]
    try:
        u = urlparse(out)
        q = dict(parse_qsl(u.query, keep_blank_values=True))
        if "sslmode" in q:
            q.pop("sslmode", None)
        new_q = urlencode(q)
        out = urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))
    except Exception:
        pass
    return out


class SQLContractsRepo(ContractsRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine = create_async_engine(_normalize_async_dsn(engine))
        else:
            self._engine = engine

    async def list(self) -> list[dict[str, Any]]:
        sql = text(
            """
            SELECT id, slug, title, chain, address, type, enabled, status, testnet,
                   methods, abi_present, webhook_url, created_at, updated_at
            FROM payment_contracts
            ORDER BY created_at DESC
            """
        )
        async with self._engine.begin() as conn:
            try:
                rows = (await conn.execute(sql)).mappings().all()
            except Exception:
                return []
            out: list[dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "id": str(r["id"]),
                        "slug": str(r["slug"]),
                        "title": r["title"],
                        "chain": r["chain"],
                        "address": r["address"],
                        "type": r["type"],
                        "enabled": bool(r["enabled"]),
                        "status": r["status"],
                        "testnet": bool(r["testnet"]),
                        "methods": dict(r["methods"]) if r["methods"] is not None else None,
                        "abi_present": bool(r["abi_present"]),
                        "webhook_url": r["webhook_url"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                    }
                )
            return out

    async def upsert(self, c: dict[str, Any]) -> dict[str, Any]:
        sql = text(
            """
            INSERT INTO payment_contracts (
              id, slug, title, chain, address, type, enabled, status, testnet,
              methods, abi_present, webhook_url, abi, created_at, updated_at
            ) VALUES (
              coalesce(:id, gen_random_uuid()), :slug, :title, :chain, :address, :type,
              coalesce(:enabled,true), coalesce(:status,'active'), coalesce(:testnet,false),
              cast(:methods as jsonb), coalesce(:abi_present,false), :webhook_url, cast(:abi as jsonb), now(), now()
            )
            ON CONFLICT (slug) DO UPDATE SET
              title = excluded.title,
              chain = excluded.chain,
              address = excluded.address,
              type = excluded.type,
              enabled = excluded.enabled,
              status = excluded.status,
              testnet = excluded.testnet,
              methods = excluded.methods,
              abi_present = excluded.abi_present,
              webhook_url = excluded.webhook_url,
              abi = excluded.abi,
              updated_at = now()
            RETURNING id, slug, title, chain, address, type, enabled, status, testnet,
                      methods, abi_present, webhook_url, created_at, updated_at
            """
        )
        payload = {
            "id": c.get("id"),
            "slug": c.get("slug"),
            "title": c.get("title"),
            "chain": c.get("chain"),
            "address": c.get("address"),
            "type": c.get("type"),
            "enabled": c.get("enabled", True),
            "status": c.get("status", "active"),
            "testnet": c.get("testnet", False),
            "methods": c.get("methods"),
            "abi_present": bool(c.get("abi_present") or bool(c.get("abi"))),
            "webhook_url": c.get("webhook_url"),
            "abi": c.get("abi"),
        }
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, payload)).mappings().first()
            assert r is not None
            return {
                "id": str(r["id"]),
                "slug": str(r["slug"]),
                "title": r["title"],
                "chain": r["chain"],
                "address": r["address"],
                "type": r["type"],
                "enabled": bool(r["enabled"]),
                "status": r["status"],
                "testnet": bool(r["testnet"]),
                "methods": dict(r["methods"]) if r["methods"] is not None else None,
                "abi_present": bool(r["abi_present"]),
                "webhook_url": r["webhook_url"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def delete(self, id_or_slug: str) -> None:
        sql = text("DELETE FROM payment_contracts WHERE id::text = :id OR slug = :id")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": id_or_slug})

    async def get(self, id_or_slug: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT id, slug, title, chain, address, type, enabled, status, testnet,
                   methods, abi_present, webhook_url, created_at, updated_at
            FROM payment_contracts
            WHERE id::text = :id OR slug = :id
            LIMIT 1
            """
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": id_or_slug})).mappings().first()
            if not r:
                return None
            return {
                "id": str(r["id"]),
                "slug": str(r["slug"]),
                "title": r["title"],
                "chain": r["chain"],
                "address": r["address"],
                "type": r["type"],
                "enabled": bool(r["enabled"]),
                "status": r["status"],
                "testnet": bool(r["testnet"]),
                "methods": dict(r["methods"]) if r["methods"] is not None else None,
                "abi_present": bool(r["abi_present"]),
                "webhook_url": r["webhook_url"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def get_by_address(self, address: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT id, slug, title, chain, address, type, enabled, status, testnet,
                   methods, abi_present, webhook_url, created_at, updated_at
            FROM payment_contracts
            WHERE lower(address) = lower(:addr)
            LIMIT 1
            """
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"addr": address})).mappings().first()
            if not r:
                return None
            return {
                "id": str(r["id"]),
                "slug": str(r["slug"]),
                "title": r["title"],
                "chain": r["chain"],
                "address": r["address"],
                "type": r["type"],
                "enabled": bool(r["enabled"]),
                "status": r["status"],
                "testnet": bool(r["testnet"]),
                "methods": dict(r["methods"]) if r["methods"] is not None else None,
                "abi_present": bool(r["abi_present"]),
                "webhook_url": r["webhook_url"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def list_events(self, id_or_slug: str | None, limit: int = 100) -> list[dict[str, Any]]:
        if id_or_slug:
            sql = text(
                """
                SELECT id, contract_id, event, method, tx_hash, status, amount, token, meta, created_at
                FROM payment_contract_events
                WHERE contract_id = (SELECT id FROM payment_contracts WHERE id::text=:id OR slug=:id)
                ORDER BY created_at DESC
                LIMIT :lim
                """
            )
            params = {"id": id_or_slug, "lim": int(max(1, min(limit, 1000)))}
        else:
            sql = text(
                """
                SELECT id, contract_id, event, method, tx_hash, status, amount, token, meta, created_at
                FROM payment_contract_events
                ORDER BY created_at DESC
                LIMIT :lim
                """
            )
            params = {"lim": int(max(1, min(limit, 1000)))}
        async with self._engine.begin() as conn:
            try:
                rows = (await conn.execute(sql, params)).mappings().all()
            except Exception:
                return []
            out: list[dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "id": str(r["id"]),
                        "contract_id": str(r["contract_id"]),
                        "event": r["event"],
                        "method": r["method"],
                        "tx_hash": r["tx_hash"],
                        "status": r["status"],
                        "amount": r["amount"],
                        "token": r["token"],
                        "meta": dict(r["meta"]) if r["meta"] is not None else None,
                        "created_at": r["created_at"],
                    }
                )
            return out

    async def add_event(self, e: dict[str, Any]) -> None:
        sql = text(
            """
            INSERT INTO payment_contract_events (id, contract_id, event, method, tx_hash, status, amount, token, meta, created_at)
            VALUES (gen_random_uuid(), :contract_id, :event, :method, :tx_hash, :status, :amount, :token, cast(:meta as jsonb), now())
            """
        )
        async with self._engine.begin() as conn:
            await conn.execute(sql, e)

    async def metrics_methods(
        self, id_or_slug: str | None, window: int = 1000
    ) -> list[dict[str, Any]]:
        if id_or_slug:
            sql = text(
                """
                SELECT method, count(*) as calls
                FROM payment_contract_events
                WHERE contract_id = (SELECT id FROM payment_contracts WHERE id::text=:id OR slug=:id)
                GROUP BY method
                ORDER BY calls DESC
                LIMIT :lim
                """
            )
            params = {"id": id_or_slug, "lim": int(max(1, min(window, 5000)))}
        else:
            sql = text(
                "SELECT method, count(*) as calls FROM payment_contract_events GROUP BY method ORDER BY calls DESC LIMIT :lim"
            )
            params = {"lim": int(max(1, min(window, 5000)))}
        async with self._engine.begin() as conn:
            try:
                rows = (await conn.execute(sql, params)).mappings().all()
            except Exception:
                return []
            return [{"method": r["method"], "calls": int(r["calls"])} for r in rows]

    async def metrics_methods_ts(
        self, id_or_slug: str | None, days: int = 30
    ) -> list[dict[str, Any]]:
        if id_or_slug:
            sql = text(
                """
                SELECT date_trunc('day', created_at) AS day, method, count(*) AS calls
                FROM payment_contract_events
                WHERE contract_id = (SELECT id FROM payment_contracts WHERE id::text=:id OR slug=:id)
                  AND created_at >= now() - (:days::text || ' days')::interval
                GROUP BY day, method
                ORDER BY day ASC
                """
            )
            params = {"id": id_or_slug, "days": int(max(1, min(days, 365)))}
        else:
            sql = text(
                """
                SELECT date_trunc('day', created_at) AS day, method, count(*) AS calls
                FROM payment_contract_events
                WHERE created_at >= now() - (:days::text || ' days')::interval
                GROUP BY day, method
                ORDER BY day ASC
                """
            )
            params = {"days": int(max(1, min(days, 365)))}
        async with self._engine.begin() as conn:
            try:
                rows = (await conn.execute(sql, params)).mappings().all()
            except Exception:
                return []
            return [
                {"day": r["day"].isoformat(), "method": r["method"], "calls": int(r["calls"])}
                for r in rows
            ]

    async def metrics_volume_ts(
        self, id_or_slug: str | None, days: int = 30
    ) -> list[dict[str, Any]]:
        if id_or_slug:
            sql = text(
                """
                SELECT date_trunc('day', created_at) AS day, coalesce(token, 'N/A') AS token, sum(coalesce(amount,0)) AS total
                FROM payment_contract_events
                WHERE contract_id = (SELECT id FROM payment_contracts WHERE id::text=:id OR slug=:id)
                  AND created_at >= now() - (:days::text || ' days')::interval
                GROUP BY day, token
                ORDER BY day ASC
                """
            )
            params = {"id": id_or_slug, "days": int(max(1, min(days, 365)))}
        else:
            sql = text(
                """
                SELECT date_trunc('day', created_at) AS day, coalesce(token, 'N/A') AS token, sum(coalesce(amount,0)) AS total
                FROM payment_contract_events
                WHERE created_at >= now() - (:days::text || ' days')::interval
                GROUP BY day, token
                ORDER BY day ASC
                """
            )
            params = {"days": int(max(1, min(days, 365)))}
        async with self._engine.begin() as conn:
            try:
                rows = (await conn.execute(sql, params)).mappings().all()
            except Exception:
                return []
            return [
                {
                    "day": r["day"].isoformat(),
                    "token": r["token"],
                    "total": float(r["total"] or 0.0),
                }
                for r in rows
            ]


__all__ = ["SQLContractsRepo"]
