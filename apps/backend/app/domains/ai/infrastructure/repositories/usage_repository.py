from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.usage_models import AIUsage


class AIUsageRepository:
    """Aggregation queries for :class:`AIUsage`."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def system_totals(self, since: datetime | None = None) -> dict[str, Any]:
        stmt = select(
            func.coalesce(func.sum(AIUsage.cost), 0.0).label("cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
        )
        if since is not None:
            stmt = stmt.where(AIUsage.ts >= since)
        row = (await self._db.execute(stmt)).one()
        return {"cost": float(row.cost or 0), "tokens": int(row.tokens or 0)}

    async def by_account(self, since: datetime | None = None) -> list[dict[str, Any]]:
        stmt = select(
            AIUsage.workspace_id,
            func.coalesce(func.sum(AIUsage.cost), 0.0).label("cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
        ).group_by(AIUsage.workspace_id)
        if since is not None:
            stmt = stmt.where(AIUsage.ts >= since)
        rows = await self._db.execute(stmt)
        out: list[dict[str, Any]] = []
        for account_id, cost, tokens in rows.all():
            out.append(
                {
                    "account_id": account_id,
                    "cost": float(cost or 0),
                    "tokens": int(tokens or 0),
                }
            )
        return out

    async def account_totals(
        self, account_id: int, since: datetime | None = None
    ) -> dict[str, Any]:
        stmt = select(
            func.coalesce(func.sum(AIUsage.cost), 0.0).label("cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
        ).where(AIUsage.workspace_id == account_id)
        if since is not None:
            stmt = stmt.where(AIUsage.ts >= since)
        row = (await self._db.execute(stmt)).one()
        return {"cost": float(row.cost or 0), "tokens": int(row.tokens or 0)}

    async def by_user(self, account_id: int, since: datetime | None = None) -> list[dict[str, Any]]:
        stmt = (
            select(
                AIUsage.user_id,
                func.coalesce(func.sum(AIUsage.cost), 0.0).label("cost"),
                func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
            )
            .where(AIUsage.workspace_id == account_id)
            .group_by(AIUsage.user_id)
        )
        if since is not None:
            stmt = stmt.where(AIUsage.ts >= since)
        rows = await self._db.execute(stmt)
        out: list[dict[str, Any]] = []
        for user_id, cost, tokens in rows.all():
            out.append(
                {
                    "user_id": user_id,
                    "cost": float(cost or 0),
                    "tokens": int(tokens or 0),
                }
            )
        return out

    async def by_model(
        self, account_id: int | None = None, since: datetime | None = None
    ) -> list[dict[str, Any]]:
        stmt = select(
            AIUsage.model,
            func.coalesce(func.sum(AIUsage.cost), 0.0).label("cost"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("tokens"),
        )
        if account_id is not None:
            stmt = stmt.where(AIUsage.workspace_id == account_id)
        if since is not None:
            stmt = stmt.where(AIUsage.ts >= since)
        stmt = stmt.group_by(AIUsage.model)
        rows = await self._db.execute(stmt)
        out: list[dict[str, Any]] = []
        for model, cost, tokens in rows.all():
            out.append(
                {
                    "model": model,
                    "cost": float(cost or 0),
                    "tokens": int(tokens or 0),
                }
            )
        return out
