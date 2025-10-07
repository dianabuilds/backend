from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.navigation.api.support import (
    coerce_int,
    isoformat,
    normalize_algo_key,
)
from domains.product.navigation.infrastructure import ensure_engine
from domains.product.navigation.infrastructure.relations import (
    fetch_strategy_rows,
    fetch_top_relations,
    fetch_usage_rows,
    update_strategy_row,
)


class RelationsAdminError(Exception):
    def __init__(self, detail: str, *, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class RelationsUnavailableError(RelationsAdminError):
    def __init__(self, detail: str = "storage_unavailable") -> None:
        super().__init__(detail, status_code=503)


class RelationsValidationError(RelationsAdminError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=400)


class RelationsNotFoundError(RelationsAdminError):
    def __init__(self, detail: str = "strategy_not_found") -> None:
        super().__init__(detail, status_code=404)


class RelationsUpdateError(RelationsAdminError):
    def __init__(self, detail: str = "update_failed") -> None:
        super().__init__(detail, status_code=500)


class RelationsAdminGateway(Protocol):
    async def get_engine(self) -> AsyncEngine | None: ...


@dataclass
class RelationsAdminService:
    gateway: RelationsAdminGateway

    async def list_strategies(self) -> list[dict[str, Any]]:
        engine = await self.gateway.get_engine()
        if engine is None:
            return []
        config = await fetch_strategy_rows(engine)
        usage = await fetch_usage_rows(engine)
        total_links = sum(info.get("links", 0) for info in usage.values())
        for item in config:
            stats = usage.get(item["strategy"], {})
            item["links"] = coerce_int(stats.get("links"), default=0) or 0
            item["score"] = float(stats.get("score", 0.0))
            item["usage_share"] = (
                float(item["links"]) / float(total_links) if total_links else 0.0
            )
        return config

    async def update_strategy(
        self, strategy: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        engine = await self.gateway.get_engine()
        if engine is None:
            raise RelationsUnavailableError()

        norm = normalize_algo_key(strategy)
        weight_val: float | None = None
        weight_raw = payload.get("weight")
        if weight_raw is not None:
            try:
                weight_val = float(weight_raw)
            except (TypeError, ValueError) as exc:
                raise RelationsValidationError("invalid_weight") from exc
            if weight_val < 0:
                raise RelationsValidationError("weight_must_be_non_negative")
        enabled_val = None
        if payload.get("enabled") is not None:
            enabled_val = bool(payload.get("enabled"))
        meta_val = payload.get("meta")
        meta_json = None
        if meta_val is not None:
            try:
                meta_json = json.dumps(meta_val)
            except (TypeError, ValueError) as exc:
                raise RelationsValidationError("invalid_meta") from exc

        row = await update_strategy_row(
            engine,
            norm,
            weight=weight_val,
            enabled=enabled_val,
            meta_json=meta_json,
        )
        if row is None:
            raise RelationsUpdateError()
        usage = await fetch_usage_rows(engine)
        total_links = sum(info.get("links", 0) for info in usage.values())
        stats = usage.get(norm, {})
        return {
            "strategy": norm,
            "weight": float(row.get("weight") or 0.0),
            "enabled": bool(row.get("enabled")),
            "updated_at": isoformat(row.get("updated_at")),
            "meta": row.get("meta") or {},
            "links": coerce_int(stats.get("links"), default=0) or 0,
            "usage_share": (
                float(stats.get("links", 0)) / float(total_links)
                if total_links
                else 0.0
            ),
        }

    async def overview(self) -> dict[str, Any]:
        engine = await self.gateway.get_engine()
        if engine is None:
            return {"strategies": [], "popular": {}, "diversity": {}}
        config = await fetch_strategy_rows(engine)
        usage = await fetch_usage_rows(engine)
        total_links = sum(info.get("links", 0) for info in usage.values())
        strategies_payload: list[dict[str, Any]] = []
        for item in config:
            stats = usage.get(item["strategy"], {})
            payload = {
                "key": item["strategy"],
                "weight": item["weight"],
                "enabled": item["enabled"],
                "updated_at": item["updated_at"],
                "links": coerce_int(stats.get("links"), default=0) or 0,
                "usage_share": (
                    float(stats.get("links", 0)) / float(total_links)
                    if total_links
                    else 0.0
                ),
            }
            strategies_payload.append(payload)
        shares = [p["usage_share"] for p in strategies_payload if p["links"] > 0]
        coverage = (
            float(len([p for p in strategies_payload if p["links"] > 0]))
            / float(len(strategies_payload))
            if strategies_payload
            else 0.0
        )
        entropy = -sum(s * math.log(s, 2) for s in shares if s > 0.0) if shares else 0.0
        gini = 1.0 - sum(s * s for s in shares) if shares else 0.0
        keys = {item["key"] for item in strategies_payload} | set(usage.keys())
        popular: dict[str, list[dict[str, Any]]] = {}
        for key in keys:
            popular[key] = await fetch_top_relations(engine, key, limit=5)
        return {
            "strategies": strategies_payload,
            "popular": popular,
            "diversity": {
                "coverage": coverage,
                "entropy": entropy,
                "gini": gini,
            },
        }

    async def top_relations(self, algo: str, *, limit: int = 10) -> dict[str, Any]:
        engine = await self.gateway.get_engine()
        if engine is None:
            return {"items": [], "strategy": normalize_algo_key(algo)}
        norm = normalize_algo_key(algo)
        items = await fetch_top_relations(engine, norm, limit=limit)
        return {"items": items, "strategy": norm}


class EngineRelationsGateway:
    def __init__(self, provider):
        self._provider = provider

    async def get_engine(self) -> AsyncEngine | None:
        return await self._provider()


def build_relations_admin_service(container: Any) -> RelationsAdminService:
    async def provider() -> AsyncEngine | None:
        return await ensure_engine(container)

    gateway = EngineRelationsGateway(provider)
    return RelationsAdminService(gateway)
