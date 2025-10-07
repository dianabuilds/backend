from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from domains.platform.audit.application.service import AuditService
from domains.platform.audit.infrastructure import AuditLogPayload, safe_audit_log
from domains.platform.audit.ports.repo import AuditLogRepository
from domains.platform.billing.ports import PlanRepo

from .exceptions import BillingUseCaseError

logger = logging.getLogger(__name__)


@dataclass
class PlansAdminUseCase:
    plans: PlanRepo
    audit_service: AuditService
    audit_repo: AuditLogRepository

    async def upsert(
        self, *, payload: dict[str, Any], actor_id: str | None
    ) -> dict[str, Any]:
        before = None
        slug = payload.get("slug")
        try:
            if slug:
                existing = await self.plans.get_by_slug(str(slug))
                before = existing.__dict__ if existing else None
        except (SQLAlchemyError, RuntimeError, ValueError) as exc:
            logger.warning(
                "Failed to load plan '%s' before update: %s", slug, exc, exc_info=exc
            )
        plan = await self.plans.upsert(payload)
        await safe_audit_log(
            self.audit_service,
            AuditLogPayload(
                actor_id=actor_id,
                action="plan.upsert",
                resource_type="plan",
                resource_id=plan.slug,
                before=before,
                after=plan.__dict__,
                extra={"route": "/v1/billing/admin/plans"},
            ),
            logger=logger,
            error_slug="billing_plan_audit_failed",
            suppressed=(SQLAlchemyError, RuntimeError),
        )
        return {"plan": plan.__dict__}

    async def delete(self, *, plan_id: str) -> dict[str, Any]:
        if not plan_id:
            raise BillingUseCaseError(status_code=400, detail="plan_id_required")
        await self.plans.delete(plan_id)
        return {"ok": True}

    async def list_all(self) -> dict[str, Any]:
        plans = await self.plans.list_all()
        return {"items": [plan.__dict__ for plan in plans]}

    async def bulk_limits(self, *, items: list[dict[str, Any]]) -> dict[str, Any]:
        updated: list[dict[str, Any]] = []
        for item in items:
            slug = str(item.get("slug") or "").strip()
            if not slug:
                continue
            existing = await self.plans.get_by_slug(slug)
            base = existing.__dict__ if existing else {}
            payload = {
                "id": base.get("id"),
                "slug": slug,
                "title": base.get("title") or slug,
                "price_cents": base.get("price_cents"),
                "currency": base.get("currency"),
                "is_active": base.get("is_active", True),
                "order": base.get("order", 100),
                "monthly_limits": item.get("monthly_limits")
                or base.get("monthly_limits"),
                "features": base.get("features"),
            }
            plan = await self.plans.upsert(payload)
            updated.append(plan.__dict__)
        return {"items": updated}

    async def audit(self, *, slug: str, limit: int = 100) -> dict[str, Any]:
        records = await self.audit_repo.list(limit=int(limit))
        filtered = [
            record
            for record in records
            if (record or {}).get("resource_type") == "plan"
            and (record or {}).get("resource_id") in {slug}
        ]
        return {"items": filtered}


__all__ = ["PlansAdminUseCase"]
