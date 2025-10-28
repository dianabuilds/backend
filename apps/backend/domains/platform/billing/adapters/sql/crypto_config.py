from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.ports import CryptoConfigRepo
from packages.core.db import get_async_engine

from ..dsn_utils import normalize_async_dsn

logger = logging.getLogger(__name__)


class SQLCryptoConfigRepo(CryptoConfigRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine = get_async_engine(
                "billing-crypto-config", url=normalize_async_dsn(engine)
            )
        else:
            self._engine = engine

    async def get(self, slug: str) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT slug,
                   rpc_endpoints,
                   fallback_networks,
                   retries,
                   gas_price_cap,
                   extra,
                   created_at,
                   updated_at
            FROM crypto_config
            WHERE slug = :slug
            """
        )
        async with self._engine.begin() as conn:
            try:
                r = (await conn.execute(sql, {"slug": slug})).mappings().first()
            except SQLAlchemyError as exc:
                logger.warning("Failed to load crypto config %s: %s", slug, exc)
                return None
            if not r:
                return None
            config = self._build_config_from_row(r)
            return {
                "slug": r["slug"],
                "config": config,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    async def set(self, slug: str, cfg: dict[str, Any]) -> dict[str, Any]:
        sql = text(
            """
            INSERT INTO crypto_config (
              slug,
              rpc_endpoints,
              fallback_networks,
              retries,
              gas_price_cap,
              extra,
              created_at,
              updated_at
            )
            VALUES (
              :slug,
              cast(:rpc_endpoints as jsonb),
              cast(:fallback_networks as jsonb),
              :retries,
              :gas_price_cap,
              cast(:extra as jsonb),
              now(),
              now()
            )
            ON CONFLICT (slug) DO UPDATE SET
              rpc_endpoints = excluded.rpc_endpoints,
              fallback_networks = excluded.fallback_networks,
              retries = excluded.retries,
              gas_price_cap = excluded.gas_price_cap,
              extra = excluded.extra,
              updated_at = now()
            RETURNING slug,
                      rpc_endpoints,
                      fallback_networks,
                      retries,
                      gas_price_cap,
                      extra,
                      created_at,
                      updated_at
            """
        )
        payload = self._split_config(slug, cfg)
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, payload)).mappings().first()
            if r is None:

                raise RuntimeError("database_row_missing")
            config = self._build_config_from_row(r)
            return {
                "slug": r["slug"],
                "config": config,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }

    @staticmethod
    def _split_config(slug: str, cfg: dict[str, Any]) -> dict[str, Any]:
        data = dict(cfg or {})
        rpc_endpoints = data.pop("rpc_endpoints", {}) or {}
        fallback_networks = data.pop("fallback_networks", {}) or {}
        retries_raw = data.pop("retries", 3)
        try:
            retries = int(retries_raw)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid retries value for crypto config %s: %r, defaulting to 3",
                slug,
                retries_raw,
            )
            retries = 3
        gas_price_cap_raw = data.pop("gas_price_cap", None)
        gas_price_cap = SQLCryptoConfigRepo._to_numeric(gas_price_cap_raw)
        extra = data if data else None
        return {
            "slug": slug,
            "rpc_endpoints": rpc_endpoints,
            "fallback_networks": fallback_networks,
            "retries": retries,
            "gas_price_cap": gas_price_cap,
            "extra": extra,
        }

    @staticmethod
    def _build_config_from_row(row: Any) -> dict[str, Any]:
        gas_price_cap = row.get("gas_price_cap")
        if isinstance(gas_price_cap, Decimal):
            gas_price_cap_value: float | None = float(gas_price_cap)
        else:
            gas_price_cap_value = (
                float(gas_price_cap) if gas_price_cap is not None else None
            )
        config: dict[str, Any] = {
            "rpc_endpoints": (
                dict(row["rpc_endpoints"])
                if row.get("rpc_endpoints") is not None
                else {}
            ),
            "fallback_networks": (
                dict(row["fallback_networks"])
                if row.get("fallback_networks") is not None
                else {}
            ),
            "retries": int(row.get("retries") or 3),
            "gas_price_cap": gas_price_cap_value,
        }
        extra = row.get("extra")
        if isinstance(extra, dict):
            config.update(extra)
        return config

    @staticmethod
    def _to_numeric(value: Any) -> float | None:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None


__all__ = ["SQLCryptoConfigRepo"]
