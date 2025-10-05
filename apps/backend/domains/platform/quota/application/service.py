from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from domains.platform.quota.ports.dao import QuotaDAO


@dataclass(slots=True)
class QuotaResult:
    allowed: bool
    remaining: int
    limit: int
    scope: str
    reset_at: str | None
    overage: bool


class QuotaService:
    def __init__(self, dao: QuotaDAO) -> None:
        self.dao = dao

    async def consume(
        self,
        *,
        user_id: str,
        key: str,
        limit: int,
        amount: int = 1,
        scope: str = "day",
        now: datetime | None = None,
        dry_run: bool = False,
    ) -> QuotaResult:
        if limit <= 0:
            return QuotaResult(
                allowed=True,
                remaining=-1,
                limit=-1,
                scope=scope,
                reset_at=None,
                overage=False,
            )

        ts = now.astimezone(UTC) if now else datetime.now(tz=UTC)
        if scope == "day":
            period = ts.strftime("%Y%m%d")
            reset_at = ts.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
        elif scope == "month":
            period = ts.strftime("%Y%m")
            first_day = ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            reset_at = (first_day + timedelta(days=32)).replace(day=1)
        else:
            raise ValueError(f"unknown scope: {scope}")
        ttl = int((reset_at - ts).total_seconds())

        if dry_run:
            current = await self.dao.get(user_id=user_id, key=key, period=period)
            new_value = current + amount
        else:
            new_value = await self.dao.incr(
                user_id=user_id,
                key=key,
                period=period,
                amount=amount,
                ttl=ttl,
            )

        allowed = new_value <= limit
        overage = new_value > limit
        remaining = max(limit - new_value, 0)

        return QuotaResult(
            allowed=allowed,
            remaining=remaining,
            limit=limit,
            scope=scope,
            reset_at=reset_at.isoformat(),
            overage=overage,
        )


__all__ = ["QuotaService", "QuotaResult"]
