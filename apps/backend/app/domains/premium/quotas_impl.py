from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache as shared_cache
from app.core.preview import PreviewContext
from app.domains.premium.application.quota_service import (
    QuotaService,
)  # общий сервис квот
from app.domains.premium.plans_impl import (
    build_quota_plans_map,
    get_effective_plan_slug,
)

_quota_service: QuotaService | None = None


def _get_qs() -> QuotaService:
    global _quota_service
    if _quota_service is None:
        _quota_service = QuotaService(cache=shared_cache)
    return _quota_service


async def check_and_consume_quota(
    db: AsyncSession,
    user_id: Any,
    *,
    quota_key: str,
    amount: int = 1,
    scope: str = "month",
    preview: PreviewContext | None = None,
    workspace_id: Any | None = None,
) -> dict:
    plans_map = await build_quota_plans_map(db)
    plan_slug = (
        preview.plan
        if preview and preview.plan
        else await get_effective_plan_slug(
            db, str(user_id) if user_id is not None else None, preview=preview
        )
    )
    qs = _get_qs()
    qs.set_plans_map(plans_map)
    return await qs.check_and_consume(
        user_id=str(user_id),
        quota_key=quota_key,
        amount=amount,
        scope=scope,
        preview=preview,
        plan=plan_slug,
        idempotency_token=None,
        workspace_id=str(workspace_id) if workspace_id is not None else None,
    )


async def get_quota_status(
    db: AsyncSession,
    user_id: Any,
    *,
    quota_key: str = "stories",
    scope: str = "month",
    preview: PreviewContext | None = None,
) -> dict:
    preview = preview or PreviewContext(mode="dry_run")
    return await check_and_consume_quota(
        db,
        user_id,
        quota_key=quota_key,
        amount=0,
        scope=scope,
        preview=preview,
    )
