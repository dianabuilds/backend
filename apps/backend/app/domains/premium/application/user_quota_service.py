from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.premium.application.quota_service import QuotaService
from app.domains.premium.application.plan_service import build_quota_plans_map, get_effective_plan_slug


_quota_service: QuotaService | None = None


def _get_qs() -> QuotaService:
    global _quota_service
    if _quota_service is None:
        _quota_service = QuotaService()
    return _quota_service


async def check_and_consume_quota(
    db: AsyncSession,
    user_id: Any,
    *,
    quota_key: str,
    amount: int = 1,
    scope: str = "month",
    dry_run: bool = False,
) -> dict:
    plans_map = await build_quota_plans_map(db)
    plan_slug = await get_effective_plan_slug(db, str(user_id) if user_id is not None else None)
    qs = _get_qs()
    qs.set_plans_map(plans_map)
    return await qs.check_and_consume(
        user_id=str(user_id),
        quota_key=quota_key,
        amount=amount,
        scope=scope,
        dry_run=dry_run,
        plan=plan_slug,
        idempotency_token=None,
    )


async def check_and_consume_story_quota(
    db: AsyncSession,
    user_id: Any,
    *,
    amount: int = 1,
    dry_run: bool = False,
    scope: str = "month",
) -> dict:
    return await check_and_consume_quota(
        db, user_id, quota_key="stories", amount=amount, scope=scope, dry_run=dry_run
    )


async def get_quota_status(
    db: AsyncSession,
    user_id: Any,
    *,
    quota_key: str = "stories",
    scope: str = "month",
) -> dict:
    return await check_and_consume_quota(
        db, user_id, quota_key=quota_key, amount=0, scope=scope, dry_run=True
    )
