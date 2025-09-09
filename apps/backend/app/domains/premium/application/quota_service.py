from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import HTTPException

from app.core.preview import PreviewContext
from app.providers.cache import Cache
from app.providers.cache import cache as shared_cache

logger = logging.getLogger(__name__)


class QuotaService:
    """Simple quota service backed by :class:`Cache`.

    The service keeps counters in the cache with keys of the form
    ``q:{quota_key}:{period}:{user_id}:{tenant_id}`` where ``period`` is
    ``YYYYMMDD`` for day scope and ``YYYYMM`` for month scope.
    """

    def __init__(self, cache: Cache | None = None, plans_file: str | None = None) -> None:
        # используем общий кэш (Redis при наличии),
        # чтобы квоты были согласованы во всех инстансах
        self.cache = cache or shared_cache
        if plans_file is None:
            plans_file = str(Path(__file__).resolve().parents[3] / "settings" / "plans.yaml")
        try:
            with open(plans_file, encoding="utf-8") as f:
                self.plans: dict[str, Any] = yaml.safe_load(f) or {}
        except FileNotFoundError:  # pragma: no cover - config missing
            logger.warning("plans configuration not found: %s", plans_file)
            self.plans = {}

    def set_plans_map(self, plans: dict[str, Any]) -> None:
        """Override plans configuration at runtime."""
        try:
            self.plans = dict(plans or {})
        except Exception:
            logger.exception("set_plans_map failed")
            # keep previous map

    async def check_and_consume(
        self,
        user_id: str,
        quota_key: str,
        amount: int = 1,
        scope: str = "day",
        *,
        preview: PreviewContext | None = None,
        plan: str | None = None,
        idempotency_token: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        if preview and preview.plan:
            plan = preview.plan
        plan = plan or "free"
        plan_conf = self.plans.get(plan, {})
        grace = float(plan_conf.get("__grace__", 0))
        limits = plan_conf.get(quota_key, {})
        limit = limits.get(scope)
        if limit is None:
            # unlimited
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "scope": scope,
                "reset_at": None,
                "overage": False,
            }

        now = preview.now.astimezone(UTC) if preview and preview.now else datetime.now(tz=UTC)
        if scope == "day":
            period = now.strftime("%Y%m%d")
            reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif scope == "month":
            period = now.strftime("%Y%m")
            first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            reset_at = (first_day + timedelta(days=32)).replace(day=1)
        else:
            raise ValueError(f"unknown scope: {scope}")
        ttl = int((reset_at - now).total_seconds())

        workspace_part = workspace_id or "-"
        counter_key = f"q:{quota_key}:{period}:{user_id}:{workspace_part}"

        # idempotency: if token exists, return stored result without modification
        if idempotency_token:
            token_key = f"qt:{idempotency_token}"
            stored = await self.cache.get(token_key)
            if stored is not None:
                return json.loads(stored)
        dry_run = preview and preview.mode == "dry_run"
        if dry_run:
            current = int(await self.cache.get(counter_key) or 0)
            new_value = current + amount
        else:
            new_value = await self.cache.incr(counter_key, amount)
            if new_value == amount:
                await self.cache.expire(counter_key, ttl)

        allowed_limit = int(limit * (1 + grace))
        allowed = new_value <= allowed_limit
        overage = new_value > limit
        remaining = max(limit - new_value, 0)

        result = {
            "allowed": allowed,
            "remaining": remaining,
            "limit": limit,
            "scope": scope,
            "reset_at": reset_at.isoformat(),
            "overage": overage,
        }

        if not dry_run and idempotency_token:
            token_key = f"qt:{idempotency_token}"
            await self.cache.set(token_key, json.dumps(result), ttl)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "quotaKey": quota_key,
                    "reset_at": result["reset_at"],
                },
            )
        return result
