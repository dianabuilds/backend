from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException

from app.core.preview import PreviewContext
from app.domains.quota.infrastructure.dao import QuotaCounterDAO


class QuotaService:
    """Service handling quota counters and limits."""

    def __init__(self, dao: QuotaCounterDAO | None = None) -> None:
        self.dao = dao or QuotaCounterDAO()

    async def consume(
        self,
        *,
        user_id: str,
        workspace_id: str,
        key: str,
        limit: int,
        amount: int = 1,
        scope: str = "day",
        preview: PreviewContext | None = None,
    ) -> dict[str, object]:
        if limit <= 0:
            return {
                "allowed": True,
                "remaining": -1,
                "limit": -1,
                "scope": scope,
                "reset_at": None,
                "overage": False,
            }

        now = (
            preview.now.astimezone(UTC)
            if preview and preview.now
            else datetime.now(tz=UTC)
        )
        if scope == "day":
            period = now.strftime("%Y%m%d")
            reset_at = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
        elif scope == "month":
            period = now.strftime("%Y%m")
            first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            reset_at = (first_day + timedelta(days=32)).replace(day=1)
        else:
            raise ValueError(f"unknown scope: {scope}")
        ttl = int((reset_at - now).total_seconds())

        dry_run = preview and preview.mode == "dry_run"
        if dry_run:
            current = await self.dao.get(
                user_id=user_id,
                workspace_id=workspace_id,
                key=key,
                period=period,
            )
            new_value = current + amount
        else:
            new_value = await self.dao.incr(
                user_id=user_id,
                workspace_id=workspace_id,
                key=key,
                period=period,
                amount=amount,
                ttl=ttl,
            )

        allowed = new_value <= limit
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

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "quotaKey": key,
                    "reset_at": result["reset_at"],
                },
            )
        return result
