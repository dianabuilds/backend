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


_PLAN_FIELDS = {
    "id",
    "slug",
    "title",
    "description",
    "price_cents",
    "currency",
    "is_active",
    "order",
    "monthly_limits",
    "features",
    "price_token",
    "price_usd_estimate",
    "billing_interval",
    "gateway_slug",
    "contract_slug",
}


def _ensure_mapping(value: Any, field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return dict(value)
    except (TypeError, ValueError) as exc:
        raise BillingUseCaseError(status_code=400, detail=f"invalid_{field}") from exc


def _sanitize_plan_payload(
    payload: dict[str, Any], base: dict[str, Any] | None = None
) -> dict[str, Any]:
    base = base or {}
    merged: dict[str, Any] = {}
    for field in _PLAN_FIELDS:
        if field in payload:
            merged[field] = payload[field]
        elif field in base:
            merged[field] = base[field]
    slug = str(merged.get("slug") or "").strip()
    if not slug:
        raise BillingUseCaseError(status_code=400, detail="slug_required")
    merged["slug"] = slug
    merged.setdefault("title", merged.get("title") or base.get("title") or slug)
    merged["billing_interval"] = str(
        merged.get("billing_interval") or base.get("billing_interval") or "month"
    )
    if "monthly_limits" in payload or "monthly_limits" in base:
        merged["monthly_limits"] = _ensure_mapping(
            merged.get("monthly_limits"), "monthly_limits"
        )
    if "features" in payload or "features" in base:
        merged["features"] = _ensure_mapping(merged.get("features"), "features")
    return merged


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
            else:
                existing = None
        except (SQLAlchemyError, RuntimeError, ValueError) as exc:
            logger.warning(
                "Failed to load plan '%s' before update: %s", slug, exc, exc_info=exc
            )
            existing = None
        base = existing.__dict__ if existing else None
        sanitized = _sanitize_plan_payload(payload, base)
        plan = await self.plans.upsert(sanitized)
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
            merged_payload = dict(base)
            merged_payload.update(item)
            merged_payload["slug"] = slug
            payload = _sanitize_plan_payload(merged_payload, base)
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
