from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.metrics import observe_contract_event
from domains.platform.billing.ports import ContractsRepo

JsonDict = dict[str, Any]
JsonDictList = list[JsonDict]
from packages.core.db import get_async_engine

from ..dsn_utils import normalize_async_dsn

logger = logging.getLogger(__name__)


class SQLContractsRepo(ContractsRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine = get_async_engine(
                "billing-contracts", url=normalize_async_dsn(engine)
            )
        else:
            self._engine = engine

    async def list(self) -> JsonDictList:
        sql = text(
            """
            SELECT id, slug, title, chain, chain_id, address, type, enabled, status, testnet,
                   methods, mint_method, burn_method, abi_present, webhook_url, webhook_secret,
                   fallback_rpc, created_at, updated_at
            FROM payment_contracts
            ORDER BY created_at DESC
            """
        )
        async with self._engine.begin() as conn:
            try:
                rows = (await conn.execute(sql)).mappings().all()
            except SQLAlchemyError as exc:
                logger.warning("Failed to list payment contracts: %s", exc)
                return []
            out: JsonDictList = []
            for r in rows:
                out.append(
                    {
                        "id": str(r["id"]),
                        "slug": str(r["slug"]),
                        "title": r["title"],
                        "chain": r["chain"],
                        "chain_id": r["chain_id"],
                        "address": r["address"],
                        "type": r["type"],
                        "enabled": bool(r["enabled"]),
                        "status": r["status"],
                        "testnet": bool(r["testnet"]),
                        "methods": (
                            dict(r["methods"]) if r["methods"] is not None else None
                        ),
                        "mint_method": r["mint_method"],
                        "burn_method": r["burn_method"],
                        "abi_present": bool(r["abi_present"]),
                        "webhook_url": r["webhook_url"],
                        "webhook_secret": r["webhook_secret"],
                        "fallback_rpc": (
                            dict(r["fallback_rpc"])
                            if r["fallback_rpc"] is not None
                            else None
                        ),
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                    }
                )
            return out

    async def upsert(self, c: JsonDict) -> JsonDict:
        sql = text(
            """
            INSERT INTO payment_contracts (
              id, slug, title, chain, chain_id, address, type, enabled, status, testnet,
              methods, mint_method, burn_method, abi_present, abi, webhook_url, webhook_secret,
              fallback_rpc, created_at, updated_at
            ) VALUES (
              coalesce(:id, gen_random_uuid()), :slug, :title, :chain, :chain_id, :address, :type,
              coalesce(:enabled,true), coalesce(:status,'active'), coalesce(:testnet,false),
              cast(:methods as jsonb), :mint_method, :burn_method,
              coalesce(:abi_present,false), cast(:abi as jsonb), :webhook_url, :webhook_secret,
              cast(:fallback_rpc as jsonb), now(), now()
            )
            ON CONFLICT (slug) DO UPDATE SET
              title = excluded.title,
              chain = excluded.chain,
              chain_id = excluded.chain_id,
              address = excluded.address,
              type = excluded.type,
              enabled = excluded.enabled,
              status = excluded.status,
              testnet = excluded.testnet,
              methods = excluded.methods,
              mint_method = excluded.mint_method,
              burn_method = excluded.burn_method,
              abi_present = excluded.abi_present,
              abi = excluded.abi,
              webhook_url = excluded.webhook_url,
              webhook_secret = excluded.webhook_secret,
              fallback_rpc = excluded.fallback_rpc,
              updated_at = now()
            RETURNING id, slug, title, chain, chain_id, address, type, enabled, status, testnet,
                      methods, mint_method, burn_method, abi_present, abi, webhook_url,
                      webhook_secret, fallback_rpc, created_at, updated_at
            """
        )
        payload = {
            "id": c.get("id"),
            "slug": c.get("slug"),
            "title": c.get("title"),
            "chain": c.get("chain"),
            "chain_id": c.get("chain_id"),
            "address": c.get("address"),
            "type": c.get("type"),
            "enabled": c.get("enabled", True),
            "status": c.get("status", "active"),
            "testnet": c.get("testnet", False),
            "methods": c.get("methods"),
            "mint_method": c.get("mint_method"),
            "burn_method": c.get("burn_method"),
            "abi_present": bool(c.get("abi_present") or bool(c.get("abi"))),
            "abi": c.get("abi"),
            "webhook_url": c.get("webhook_url"),
            "webhook_secret": c.get("webhook_secret"),
            "fallback_rpc": c.get("fallback_rpc"),
        }
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, payload)).mappings().first()
            if r is None:

                raise RuntimeError("database_row_missing")
            return {
                "id": str(r["id"]),
                "slug": str(r["slug"]),
                "title": r["title"],
                "chain": r["chain"],
                "chain_id": r["chain_id"],
                "address": r["address"],
                "type": r["type"],
                "enabled": bool(r["enabled"]),
                "status": r["status"],
                "testnet": bool(r["testnet"]),
                "methods": dict(r["methods"]) if r["methods"] is not None else None,
                "mint_method": r["mint_method"],
                "burn_method": r["burn_method"],
                "abi_present": bool(r["abi_present"]),
                "abi": r["abi"],
                "webhook_url": r["webhook_url"],
                "webhook_secret": r["webhook_secret"],
                "fallback_rpc": (
                    dict(r["fallback_rpc"]) if r["fallback_rpc"] is not None else None
                ),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def delete(self, id_or_slug: str) -> None:
        sql = text("DELETE FROM payment_contracts WHERE id::text = :id OR slug = :id")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": id_or_slug})

    async def get(self, id_or_slug: str) -> JsonDict | None:
        sql = text(
            """
            SELECT id, slug, title, chain, chain_id, address, type, enabled, status, testnet,
                   methods, mint_method, burn_method, abi_present, abi, webhook_url,
                   webhook_secret, fallback_rpc, created_at, updated_at
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
                "chain_id": r["chain_id"],
                "address": r["address"],
                "type": r["type"],
                "enabled": bool(r["enabled"]),
                "status": r["status"],
                "testnet": bool(r["testnet"]),
                "methods": dict(r["methods"]) if r["methods"] is not None else None,
                "mint_method": r["mint_method"],
                "burn_method": r["burn_method"],
                "abi_present": bool(r["abi_present"]),
                "abi": r["abi"],
                "webhook_url": r["webhook_url"],
                "webhook_secret": r["webhook_secret"],
                "fallback_rpc": (
                    dict(r["fallback_rpc"]) if r["fallback_rpc"] is not None else None
                ),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def get_by_address(self, address: str) -> JsonDict | None:
        sql = text(
            """
            SELECT id, slug, title, chain, chain_id, address, type, enabled, status, testnet,
                   methods, mint_method, burn_method, abi_present, abi, webhook_url,
                   webhook_secret, fallback_rpc, created_at, updated_at
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
                "chain_id": r["chain_id"],
                "address": r["address"],
                "type": r["type"],
                "enabled": bool(r["enabled"]),
                "status": r["status"],
                "testnet": bool(r["testnet"]),
                "methods": dict(r["methods"]) if r["methods"] is not None else None,
                "mint_method": r["mint_method"],
                "burn_method": r["burn_method"],
                "abi_present": bool(r["abi_present"]),
                "abi": r["abi"],
                "webhook_url": r["webhook_url"],
                "webhook_secret": r["webhook_secret"],
                "fallback_rpc": (
                    dict(r["fallback_rpc"]) if r["fallback_rpc"] is not None else None
                ),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def list_events(
        self, id_or_slug: str | None, limit: int = 100
    ) -> JsonDictList:
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
            except SQLAlchemyError as exc:
                logger.warning("Failed to list payment contract events: %s", exc)
                return []
            out: JsonDictList = []
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

    async def add_event(self, e: JsonDict) -> None:
        sql = text(
            """
            INSERT INTO payment_contract_events (id, contract_id, event, method, tx_hash, status, amount, token, meta, created_at)
            VALUES (gen_random_uuid(), :contract_id, :event, :method, :tx_hash, :status, :amount, :token, cast(:meta as jsonb), now())
            """
        )
        payload = {
            "contract_id": e.get("contract_id"),
            "event": e.get("event"),
            "method": e.get("method"),
            "tx_hash": e.get("tx_hash"),
            "status": e.get("status"),
            "amount": e.get("amount"),
            "token": e.get("token"),
            "meta": e.get("meta"),
        }
        async with self._engine.begin() as conn:
            await conn.execute(sql, payload)
        observe_contract_event(
            event=e.get("event"),
            status=e.get("status"),
            chain_id=e.get("chain_id"),
            method=e.get("method"),
        )

    async def metrics_methods(
        self, id_or_slug: str | None, window: int = 1000
    ) -> JsonDictList:
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
            except SQLAlchemyError as exc:
                logger.warning("Failed to fetch contract method metrics: %s", exc)
                return []
            return [{"method": r["method"], "calls": int(r["calls"])} for r in rows]

    async def metrics_methods_ts(
        self, id_or_slug: str | None, days: int = 30
    ) -> JsonDictList:
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
            except SQLAlchemyError as exc:
                logger.warning(
                    "Failed to fetch contract method time-series metrics: %s", exc
                )
                return []
            return [
                {
                    "day": r["day"].isoformat(),
                    "method": r["method"],
                    "calls": int(r["calls"]),
                }
                for r in rows
            ]

    async def metrics_volume_ts(
        self, id_or_slug: str | None, days: int = 30
    ) -> JsonDictList:
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
            except SQLAlchemyError as exc:
                logger.warning(
                    "Failed to fetch contract volume time-series metrics: %s", exc
                )
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
