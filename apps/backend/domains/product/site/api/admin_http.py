from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, ConfigDict, Field, root_validator

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_role_db,
)
from domains.product.content.api.home_http import get_home_composer
from domains.product.content.domain.models import HomeConfig, HomeConfigStatus
from domains.product.site.application import SiteService
from domains.product.site.application.block_preview import (
    get_block_preview as build_block_preview,
)
from domains.product.site.domain import (
    BlockBinding,
    BlockMetrics,
    BlockScope,
    BlockStatus,
    BlockTemplate,
    BlockTopPage,
    MetricAlert,
    MetricValue,
    PageMetrics,
    PageReviewStatus,
    PageStatus,
    PageType,
    SitePageNotFound,
    SiteRepositoryError,
    SiteValidationError,
)
from domains.product.site.infrastructure.repositories import helpers as repo_helpers


def _serialize_page(
    page, *, shared_bindings: Sequence[BlockBinding] | None = None
) -> dict[str, Any]:
    return {
        "id": str(page.id),
        "slug": page.slug,
        "type": page.type.value,
        "status": page.status.value,
        "title": page.title,
        "locale": page.locale,
        "default_locale": page.default_locale,
        "available_locales": list(page.available_locales),
        "slug_localized": dict(page.slug_localized or {}),
        "owner": page.owner,
        "created_at": page.created_at.isoformat(),
        "updated_at": page.updated_at.isoformat(),
        "published_version": page.published_version,
        "draft_version": page.draft_version,
        "has_pending_review": page.has_pending_review,
        "pinned": page.pinned,
        "shared_bindings": (
            [_serialize_block_binding(binding) for binding in shared_bindings]
            if shared_bindings is not None
            else None
        ),
    }


def _serialize_draft(
    draft,
    *,
    shared_bindings: Sequence[BlockBinding] | None = None,
    global_blocks: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "page_id": str(draft.page_id),
        "version": draft.version,
        "data": draft.data,
        "meta": draft.meta,
        "comment": draft.comment,
        "review_status": draft.review_status.value,
        "updated_at": draft.updated_at.isoformat(),
        "updated_by": draft.updated_by,
        "block_refs": (
            _serialize_page_block_refs(global_blocks)
            if global_blocks is not None
            else repo_helpers.format_shared_block_refs(draft.data, draft.meta)
        ),
        "shared_bindings": (
            [_serialize_block_binding(binding) for binding in shared_bindings]
            if shared_bindings is not None
            else None
        ),
    }


def _serialize_version(version) -> dict[str, Any]:
    return {
        "id": str(version.id),
        "page_id": str(version.page_id),
        "version": version.version,
        "data": version.data,
        "meta": version.meta,
        "comment": version.comment,
        "diff": version.diff,
        "published_at": version.published_at.isoformat(),
        "published_by": version.published_by,
        "block_refs": repo_helpers.format_shared_block_refs(version.data, version.meta),
    }


def _serialize_page_block_refs(
    blocks: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for block in blocks:
        item = {
            "block_id": block.get("block_id"),
            "key": block.get("key"),
            "title": block.get("title"),
            "section": block.get("section"),
            "scope": block.get("scope", "shared"),
            "status": block.get("status"),
            "locale": block.get("default_locale"),
            "default_locale": block.get("default_locale"),
            "available_locales": list(block.get("available_locales") or []),
            "requires_publisher": bool(block.get("requires_publisher")),
            "published_version": block.get("published_version"),
            "draft_version": block.get("draft_version"),
            "review_status": block.get("review_status"),
            "updated_by": block.get("updated_by"),
        }
        updated_at = block.get("updated_at")
        if isinstance(updated_at, datetime):
            item["updated_at"] = updated_at.isoformat()
        elif updated_at is not None:
            item["updated_at"] = str(updated_at)
        else:
            item["updated_at"] = None
        serialized.append(item)
    return serialized


def _serialize_block_binding(binding: BlockBinding) -> dict[str, Any]:
    extras = dict(binding.extras or {})
    if binding.active is False and "is_missing" not in extras:
        extras["is_missing"] = True
    return {
        "block_id": str(binding.block_id),
        "page_id": str(binding.page_id),
        "section": binding.section,
        "locale": binding.locale,
        "has_draft": binding.has_draft,
        "has_draft_binding": binding.has_draft,
        "last_published_at": (
            binding.last_published_at.isoformat() if binding.last_published_at else None
        ),
        "active": binding.active,
        "position": binding.position,
        "title": binding.title,
        "key": binding.key,
        "slug": binding.slug,
        "page_status": (
            binding.page_status.value
            if isinstance(binding.page_status, PageStatus)
            else (str(binding.page_status) if binding.page_status is not None else None)
        ),
        "owner": binding.owner,
        "default_locale": binding.default_locale,
        "available_locales": list(binding.available_locales or ()),
        "scope": (
            binding.scope.value
            if isinstance(binding.scope, BlockScope)
            else binding.scope
        ),
        "requires_publisher": binding.requires_publisher,
        "status": (
            binding.status.value
            if isinstance(binding.status, BlockStatus)
            else (str(binding.status) if binding.status is not None else None)
        ),
        "review_status": (
            binding.review_status.value
            if isinstance(binding.review_status, PageReviewStatus)
            else (
                str(binding.review_status)
                if binding.review_status is not None
                else None
            )
        ),
        "updated_at": binding.updated_at.isoformat() if binding.updated_at else None,
        "extras": extras,
    }


def _serialize_block(block) -> dict[str, Any]:
    return {
        "id": str(block.id),
        "key": block.key,
        "title": block.title,
        "template_id": str(block.template_id) if block.template_id else None,
        "template_key": block.template_key,
        "section": block.section,
        "scope": block.scope.value,
        "locale": block.locale,
        "default_locale": block.default_locale,
        "available_locales": list(block.available_locales),
        "status": block.status.value,
        "review_status": block.review_status.value,
        "data": block.data,
        "meta": block.meta,
        "updated_at": block.updated_at.isoformat(),
        "updated_by": block.updated_by,
        "published_version": block.published_version,
        "draft_version": block.draft_version,
        "version": block.version,
        "requires_publisher": block.requires_publisher,
        "comment": block.comment,
        "usage_count": int(block.usage_count or 0),
        "extras": dict(block.extras or {}),
        "has_pending_publish": (block.draft_version or 0)
        > (block.published_version or 0),
        "is_template": block.is_template,
        "origin_block_id": (
            str(block.origin_block_id) if block.origin_block_id else None
        ),
    }


def _serialize_block_template(template: BlockTemplate) -> dict[str, Any]:
    return {
        "id": str(template.id),
        "key": template.key,
        "title": template.title,
        "section": template.section,
        "description": template.description,
        "status": template.status,
        "default_locale": template.default_locale,
        "available_locales": list(template.available_locales),
        "default_data": template.default_data,
        "default_meta": template.default_meta,
        "block_type": template.block_type,
        "category": template.category,
        "sources": list(template.sources),
        "surfaces": list(template.surfaces),
        "owners": list(template.owners),
        "catalog_locales": list(template.catalog_locales),
        "documentation_url": template.documentation_url,
        "keywords": list(template.keywords),
        "preview_kind": template.preview_kind,
        "status_note": template.status_note,
        "requires_publisher": template.requires_publisher,
        "allow_shared_scope": template.allow_shared_scope,
        "allow_page_scope": template.allow_page_scope,
        "shared_note": template.shared_note,
        "key_prefix": template.key_prefix,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "created_by": template.created_by,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        "updated_by": template.updated_by,
    }


def _serialize_usage(usage) -> dict[str, Any]:
    return {
        "block_id": str(usage.block_id),
        "page_id": str(usage.page_id),
        "slug": usage.slug,
        "title": usage.title,
        "status": usage.status.value,
        "section": usage.section,
        "locale": usage.locale,
        "has_draft": bool(usage.has_draft),
        "last_published_at": (
            usage.last_published_at.isoformat() if usage.last_published_at else None
        ),
    }


def _serialize_block_version(version) -> dict[str, Any]:
    return {
        "id": str(version.id),
        "block_id": str(version.block_id),
        "version": version.version,
        "data": version.data,
        "meta": version.meta,
        "comment": version.comment,
        "diff": version.diff,
        "published_at": version.published_at.isoformat(),
        "published_by": version.published_by,
    }


def _serialize_metric_value(metric: MetricValue) -> dict[str, Any]:
    payload: dict[str, Any] = {"value": metric.value}
    if metric.delta is not None:
        payload["delta"] = metric.delta
    if metric.unit:
        payload["unit"] = metric.unit
    if metric.trend:
        payload["trend"] = list(metric.trend)
    return payload


def _serialize_metric_alert(alert: MetricAlert) -> dict[str, Any]:
    return {
        "code": alert.code,
        "message": alert.message,
        "severity": alert.severity.value,
    }


def _serialize_top_page(item: BlockTopPage) -> dict[str, Any]:
    return {
        "page_id": str(item.page_id),
        "slug": item.slug,
        "title": item.title,
        "impressions": item.impressions,
        "clicks": item.clicks,
        "ctr": item.ctr,
    }


def _serialize_page_metrics(metrics: PageMetrics) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "page_id": str(metrics.page_id),
        "period": metrics.period,
        "range": {
            "start": metrics.range_start.isoformat(),
            "end": metrics.range_end.isoformat(),
        },
        "status": metrics.status,
        "source_lag_ms": metrics.source_lag_ms,
        "metrics": {
            name: _serialize_metric_value(value)
            for name, value in metrics.metrics.items()
        },
        "alerts": [_serialize_metric_alert(alert) for alert in metrics.alerts],
    }
    if metrics.previous_range_start and metrics.previous_range_end:
        payload["previous_range"] = {
            "start": metrics.previous_range_start.isoformat(),
            "end": metrics.previous_range_end.isoformat(),
        }
    return payload


def _serialize_block_metrics(metrics: BlockMetrics) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "block_id": str(metrics.block_id),
        "period": metrics.period,
        "range": {
            "start": metrics.range_start.isoformat(),
            "end": metrics.range_end.isoformat(),
        },
        "status": metrics.status,
        "source_lag_ms": metrics.source_lag_ms,
        "metrics": {
            name: _serialize_metric_value(value)
            for name, value in metrics.metrics.items()
        },
        "alerts": [_serialize_metric_alert(alert) for alert in metrics.alerts],
        "top_pages": [_serialize_top_page(item) for item in metrics.top_pages],
    }
    if metrics.previous_range_start and metrics.previous_range_end:
        payload["previous_range"] = {
            "start": metrics.previous_range_start.isoformat(),
            "end": metrics.previous_range_end.isoformat(),
        }
    return payload


DEFAULT_PREVIEW_LAYOUTS: tuple[str, ...] = ("desktop", "mobile")


def _serialize_validation_errors(error: SiteValidationError) -> dict[str, Any]:
    return {
        "code": error.code,
        "errors": {
            "general": [dict(item) for item in error.general_errors],
            "blocks": {
                block_id: [dict(entry) for entry in entries]
                for block_id, entries in error.block_errors.items()
            },
        },
    }


def _normalize_preview_layouts(layouts: Sequence[str] | None) -> list[str]:
    if not layouts:
        return list(DEFAULT_PREVIEW_LAYOUTS)
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in layouts:
        if not isinstance(raw, str):
            continue
        candidate = raw.strip().lower()
        if candidate not in {"desktop", "mobile"}:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized or list(DEFAULT_PREVIEW_LAYOUTS)


class PageCreatePayload(BaseModel):
    slug: str = Field(min_length=1, max_length=255)
    type: PageType
    title: str = Field(min_length=1, max_length=255)
    locale: str = Field(default="ru", min_length=2, max_length=8)
    owner: str | None = Field(default=None, max_length=255)
    pinned: bool = Field(default=False)


class PageUpdatePayload(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    locale: str | None = Field(default=None, min_length=2, max_length=8)
    owner: str | None = Field(default=None, max_length=255)
    pinned: bool | None = None


class PageDraftPayload(BaseModel):
    version: int = Field(ge=0)
    data: Mapping[str, Any] = Field(default_factory=dict)
    meta: Mapping[str, Any] = Field(default_factory=dict)
    comment: str | None = Field(default=None, max_length=500)
    review_status: PageReviewStatus = Field(default=PageReviewStatus.NONE)


class PublishPayload(BaseModel):
    comment: str | None = Field(default=None, max_length=500)
    diff: list[Mapping[str, Any]] | None = None


class DraftValidationPayload(BaseModel):
    data: Mapping[str, Any] = Field(default_factory=dict)
    meta: Mapping[str, Any] = Field(default_factory=dict)


class PagePreviewPayload(DraftValidationPayload):
    layouts: list[str] | None = Field(default=None, max_length=4)
    version: int | None = Field(default=None, ge=0)


class ReviewPayload(BaseModel):
    status: PageReviewStatus
    comment: str | None = Field(default=None, max_length=500)


class BlockSavePayload(BaseModel):
    version: int | None = Field(default=None, ge=0)
    data: Mapping[str, Any] = Field(default_factory=dict)
    meta: Mapping[str, Any] = Field(default_factory=dict)
    comment: str | None = Field(default=None, max_length=500)
    review_status: PageReviewStatus = Field(default=PageReviewStatus.NONE)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    section: str | None = Field(default=None, min_length=1, max_length=64)
    default_locale: str | None = Field(default=None, min_length=2, max_length=8)
    available_locales: list[str] | None = Field(default=None, max_length=8)
    requires_publisher: bool | None = None


class BlockCreatePayload(BaseModel):
    key: str | None = Field(default=None, min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    template_id: UUID | None = Field(default=None)
    template_key: str | None = Field(default=None, min_length=1, max_length=128)
    section: str = Field(default="promo", min_length=1, max_length=64)
    scope: BlockScope = Field(default=BlockScope.SHARED)
    default_locale: str | None = Field(default="ru", min_length=2, max_length=8)
    available_locales: list[str] | None = Field(default=None, max_length=8)
    requires_publisher: bool = Field(default=False)
    data: Mapping[str, Any] = Field(default_factory=dict)
    meta: Mapping[str, Any] = Field(default_factory=dict)
    is_template: bool = Field(default=False)
    origin_block_id: UUID | None = Field(default=None)


class BlockTemplateCreatePayload(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    section: str = Field(default="general", min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
    status: str = Field(default="available", min_length=1, max_length=32)
    default_locale: str | None = Field(default="ru", min_length=2, max_length=8)
    available_locales: list[str] | None = Field(default=None, max_length=16)
    block_type: str | None = Field(default=None, min_length=1, max_length=64)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    sources: list[str] | None = Field(default=None, max_length=16)
    surfaces: list[str] | None = Field(default=None, max_length=16)
    owners: list[str] | None = Field(default=None, max_length=16)
    catalog_locales: list[str] | None = Field(default=None, max_length=16)
    documentation_url: str | None = Field(default=None, max_length=2000)
    keywords: list[str] | None = Field(default=None, max_length=32)
    preview_kind: str | None = Field(default=None, min_length=1, max_length=64)
    status_note: str | None = Field(default=None, max_length=1000)
    requires_publisher: bool = Field(default=False)
    allow_shared_scope: bool = Field(default=True)
    allow_page_scope: bool = Field(default=True)
    shared_note: str | None = Field(default=None, max_length=1000)
    key_prefix: str | None = Field(default=None, max_length=128)
    default_data: Mapping[str, Any] = Field(default_factory=dict)
    default_meta: Mapping[str, Any] = Field(default_factory=dict)

    @root_validator(pre=True)
    def _normalize_default_payload(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "default_data" not in values and "data" in values:
            values["default_data"] = values.pop("data")
        if "default_meta" not in values and "meta" in values:
            values["default_meta"] = values.pop("meta")
        return values

    model_config = ConfigDict(validate_by_name=True)


class BlockTemplateUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    section: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
    status: str | None = Field(default=None, min_length=1, max_length=32)
    default_locale: str | None = Field(default=None, min_length=2, max_length=8)
    available_locales: list[str] | None = Field(default=None, max_length=16)
    block_type: str | None = Field(default=None, min_length=1, max_length=64)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    sources: list[str] | None = Field(default=None, max_length=16)
    surfaces: list[str] | None = Field(default=None, max_length=16)
    owners: list[str] | None = Field(default=None, max_length=16)
    catalog_locales: list[str] | None = Field(default=None, max_length=16)
    documentation_url: str | None = Field(default=None, max_length=2000)
    keywords: list[str] | None = Field(default=None, max_length=32)
    preview_kind: str | None = Field(default=None, min_length=1, max_length=64)
    status_note: str | None = Field(default=None, max_length=1000)
    requires_publisher: bool | None = Field(default=None)
    allow_shared_scope: bool | None = Field(default=None)
    allow_page_scope: bool | None = Field(default=None)
    shared_note: str | None = Field(default=None, max_length=1000)
    key_prefix: str | None = Field(default=None, max_length=128)
    default_data: Mapping[str, Any] | None = Field(default=None)
    default_meta: Mapping[str, Any] | None = Field(default=None)

    @root_validator(pre=True)
    def _normalize_default_updates(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "default_data" not in values and "data" in values:
            values["default_data"] = values.pop("data")
        if "default_meta" not in values and "meta" in values:
            values["default_meta"] = values.pop("meta")
        return values

    model_config = ConfigDict(validate_by_name=True)


class BlockPublishPayload(BaseModel):
    comment: str | None = Field(default=None, max_length=500)
    diff: list[Mapping[str, Any]] | None = None
    version: int | None = Field(default=None, ge=0)
    acknowledge_usage: bool = Field(default=False)


class BlockArchivePayload(BaseModel):
    restore: bool = Field(default=False)


class SharedBindingAssignPayload(BaseModel):
    block_id: UUID
    locale: str | None = Field(default=None, min_length=2, max_length=8)


class AuditQuery(BaseModel):
    entity_type: str | None = None
    entity_id: UUID | None = None
    actor: str | None = None
    limit: int = 50
    offset: int = 0


def get_site_service(container=Depends(get_container)) -> SiteService:
    service = getattr(container, "site_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="site_service_unavailable",
        )
    return service


router = APIRouter(prefix="/v1/site", tags=["site"])

_KNOWN_ROLES = {"user", "editor", "support", "moderator", "admin"}
_ROLE_ALIASES = {
    "site.viewer": "user",
    "site.editor": "editor",
    "site.publisher": "editor",
    "site.reviewer": "moderator",
    "site.admin": "admin",
    "platform.admin": "admin",
    "platform.moderator": "moderator",
    "finance_ops": "support",
}


_PAGE_UPDATE_VALIDATION_ERRORS = {
    "site_page_invalid_slug",
    "site_page_invalid_title",
    "site_page_invalid_locale",
    "site_page_invalid_owner",
    "site_page_invalid_pinned",
}


@router.get(
    "/blocks/{block_id}/preview",
    dependencies=[Depends(require_role_db("editor"))],
)
async def preview_block(
    block_id: str,
    locale: str = Query(default="ru"),
    limit: int = Query(default=6, ge=1, le=12),
    container=Depends(get_container),
) -> dict[str, Any]:
    return await build_block_preview(container, block_id, locale=locale, limit=limit)


def _add_role(target: set[str], value: Any) -> None:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return
        alias = _ROLE_ALIASES.get(normalized, normalized)
        if alias in _KNOWN_ROLES:
            target.add(alias)


def _collect_site_roles(claims: Mapping[str, Any]) -> set[str]:
    roles: set[str] = set()
    _add_role(roles, claims.get("role"))
    for key in ("roles", "site_roles", "permissions", "scopes"):
        raw = claims.get(key)
        if isinstance(raw, str):
            _add_role(roles, raw)
        elif isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
            for item in raw:
                _add_role(roles, item)
    return roles


def _resolve_team(claims: Mapping[str, Any]) -> str | None:
    for key in ("team", "team_id"):
        raw = claims.get(key)
        if isinstance(raw, str):
            candidate = raw.strip()
            if candidate:
                return candidate
    for key in ("teams", "team_codes"):
        raw = claims.get(key)
        if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
            for item in raw:
                if isinstance(item, str):
                    candidate = item.strip()
                    if candidate:
                        return candidate
    return None


def _resolve_actor(claims: Mapping[str, Any]) -> str | None:
    raw = claims.get("sub")
    if isinstance(raw, str):
        candidate = raw.strip()
        if candidate:
            return candidate
    return None


@router.get(
    "/pages",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_pages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    page_type: PageType | None = Query(default=None, alias="type"),
    status: PageStatus | None = Query(default=None),
    locale: str | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1),
    has_draft: bool | None = Query(default=None),
    pinned: bool | None = Query(default=None),
    sort: str = Query(
        "updated_at_desc",
        pattern="^(updated_at_desc|updated_at_asc|title_asc|title_desc|pinned_desc|pinned_asc)$",
    ),
    claims: Mapping[str, Any] = Depends(get_current_user),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    roles = _collect_site_roles(claims)
    team = _resolve_team(claims)
    actor = _resolve_actor(claims)
    pages, total = await service.list_pages(
        page=page,
        page_size=page_size,
        page_type=page_type,
        status=status,
        locale=locale,
        query=q,
        has_draft=has_draft,
        sort=sort,
        pinned=pinned,
        viewer_roles=roles,
        viewer_team=team,
        viewer_id=actor,
    )
    return {
        "items": [_serialize_page(item) for item in pages],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/pages",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def create_page(
    request: Request,
    payload: PageCreatePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    page = await service.create_page(
        slug=payload.slug,
        page_type=payload.type,
        title=payload.title,
        locale=payload.locale,
        owner=payload.owner,
        actor=actor,
        pinned=payload.pinned,
    )
    return _serialize_page(page)


@router.patch(
    "/pages/{page_id}",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def update_page(
    request: Request,
    page_id: UUID,
    payload: PageUpdatePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    fields = payload.model_dump(exclude_unset=True)
    try:
        page = await service.update_page(page_id=page_id, actor=actor, **fields)
    except SitePageNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SiteRepositoryError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_400_BAD_REQUEST
            if detail in _PAGE_UPDATE_VALIDATION_ERRORS
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code, detail=detail) from exc
    return _serialize_page(page)


@router.delete(
    "/pages/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def delete_page(
    request: Request,
    page_id: UUID,
    service: SiteService = Depends(get_site_service),
) -> Response:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    try:
        await service.delete_page(page_id=page_id, actor=actor)
    except SitePageNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/pages/{page_id}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_page(
    page_id: UUID,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        page = await service.get_page(page_id)
    except SiteRepositoryError as exc:  # pragma: no cover - defensive
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    blocks = await service.list_page_global_blocks(page_id)
    bindings = await service.list_page_shared_bindings(page_id)
    payload = _serialize_page(page, shared_bindings=bindings)
    payload["block_refs"] = _serialize_page_block_refs(blocks)
    return payload


@router.get(
    "/pages/{page_id}/draft",
    dependencies=[Depends(require_role_db("editor"))],
)
async def get_page_draft(
    page_id: UUID,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    draft = await service.get_page_draft(page_id)
    bindings = await service.list_page_shared_bindings(page_id, include_inactive=True)
    blocks = await service.list_page_global_blocks(page_id, include_inactive=True)
    return _serialize_draft(
        draft,
        shared_bindings=bindings,
        global_blocks=blocks,
    )


@router.get(
    "/pages/{page_id}/shared-bindings",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_shared_bindings(
    page_id: UUID,
    locale: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    bindings = await service.list_page_shared_bindings(
        page_id,
        locale=locale,
        include_inactive=include_inactive,
    )
    return {"items": [_serialize_block_binding(binding) for binding in bindings]}


@router.put(
    "/pages/{page_id}/shared-bindings/{section}",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def assign_shared_binding(
    request: Request,
    page_id: UUID,
    section: str,
    payload: SharedBindingAssignPayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    await get_current_user(request)
    binding = await service.assign_shared_block(
        page_id,
        section=section,
        block_id=payload.block_id,
        locale=payload.locale,
    )
    return _serialize_block_binding(binding)


@router.delete(
    "/pages/{page_id}/shared-bindings/{section}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def delete_shared_binding(
    request: Request,
    page_id: UUID,
    section: str,
    locale: str | None = Query(default=None),
    service: SiteService = Depends(get_site_service),
) -> Response:
    await get_current_user(request)
    await service.remove_shared_block(page_id, section=section, locale=locale)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/pages/{page_id}/draft",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def save_page_draft(
    request: Request,
    page_id: UUID,
    payload: PageDraftPayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    try:
        draft = await service.save_page_draft(
            page_id=page_id,
            payload=payload.data,
            meta=payload.meta,
            comment=payload.comment,
            review_status=payload.review_status,
            expected_version=payload.version,
            actor=actor,
        )
    except SiteValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_serialize_validation_errors(exc),
        ) from exc
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize_draft(draft)


@router.post(
    "/pages/{page_id}/draft/validate",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def validate_page_draft(
    page_id: UUID,
    payload: DraftValidationPayload = Body(default=DraftValidationPayload()),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        validated = service.validate_draft_payload(
            payload=payload.data,
            meta=payload.meta,
        )
    except SiteValidationError as exc:
        detail = _serialize_validation_errors(exc)
        return {
            "valid": False,
            "code": detail["code"],
            "errors": detail["errors"],
        }
    return {
        "valid": True,
        "data": validated.data,
        "meta": validated.meta,
    }


@router.get(
    "/pages/{page_id}/draft/diff",
    dependencies=[Depends(require_role_db("editor"))],
)
async def diff_page_draft(
    page_id: UUID,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    diff, draft_version, published_version = await service.diff_page_draft(page_id)
    return {
        "page_id": str(page_id),
        "draft_version": draft_version,
        "published_version": published_version,
        "diff": diff,
    }


@router.post(
    "/pages/{page_id}/preview",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def preview_page(
    page_id: UUID,
    payload: PagePreviewPayload = Body(default=PagePreviewPayload()),
    service: SiteService = Depends(get_site_service),
    container=Depends(get_container),
) -> dict[str, Any]:
    try:
        page = await service.get_page(page_id)
        draft = await service.get_page_draft(page_id)
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    layouts = _normalize_preview_layouts(payload.layouts)
    try:
        validated = service.validate_draft_payload(
            payload=payload.data if payload.data else draft.data,
            meta=payload.meta if payload.meta else draft.meta,
        )
    except SiteValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_serialize_validation_errors(exc),
        ) from exc
    composer = get_home_composer(container)
    preview_config = _build_site_preview_config(
        page=page,
        draft=draft,
        payload=validated.data,
        meta=validated.meta,
    )
    rendered_payload = await composer.compose(preview_config, use_cache=False)
    generated_at = rendered_payload.get("generated_at") or datetime.now(
        UTC
    ).isoformat().replace("+00:00", "Z")
    layout_payload = {
        layout: {
            "layout": layout,
            "generated_at": generated_at,
            "data": deepcopy(validated.data),
            "meta": deepcopy(validated.meta),
            "payload": deepcopy(rendered_payload),
        }
        for layout in layouts
    }
    version_mismatch = payload.version is not None and payload.version != draft.version
    return {
        "page": _serialize_page(page),
        "draft_version": draft.version,
        "published_version": page.published_version,
        "requested_version": payload.version,
        "version_mismatch": version_mismatch,
        "layouts": layout_payload,
    }


@router.post(
    "/pages/{page_id}/publish",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def publish_page(
    request: Request,
    page_id: UUID,
    payload: PublishPayload = Body(default=PublishPayload()),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    try:
        version = await service.publish_page(
            page_id=page_id,
            actor=actor,
            comment=payload.comment,
            diff=payload.diff,
        )
    except SiteValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_serialize_validation_errors(exc),
        ) from exc
    except SiteRepositoryError as exc:  # pragma: no cover - defensive
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize_version(version)


@router.get(
    "/pages/{page_id}/history",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_page_history(
    page_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    versions, total = await service.list_page_history(
        page_id, limit=limit, offset=offset
    )
    return {
        "items": [_serialize_version(v) for v in versions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/pages/{page_id}/history/{version}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_page_version(
    page_id: UUID,
    version: int,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        version_obj = await service.get_page_version(page_id, version)
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize_version(version_obj)


@router.get(
    "/pages/{page_id}/metrics",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_page_metrics(
    page_id: UUID,
    period: str = Query(default="7d", pattern="^(1d|7d|30d)$"),
    locale: str = Query(default="ru", min_length=2, max_length=8),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        metrics = await service.get_page_metrics(page_id, period=period, locale=locale)
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if metrics is None:
        return {
            "page_id": str(page_id),
            "period": period,
            "status": "no_data",
            "metrics": {},
            "alerts": [],
        }
    return _serialize_page_metrics(metrics)


@router.post(
    "/pages/{page_id}/history/{version}/restore",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def restore_page_version(
    request: Request,
    page_id: UUID,
    version: int,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    draft = await service.restore_page_version(page_id, version, actor=actor)
    return _serialize_draft(draft)


@router.get(
    "/blocks",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_blocks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    scope: list[BlockScope] | None = Query(default=None),
    section: str | None = Query(default=None),
    status: BlockStatus | None = Query(default=None),
    locale: str | None = Query(default=None),
    q: str | None = Query(default=None),
    has_draft: bool | None = Query(default=None),
    requires_publisher: bool | None = Query(default=None),
    review_status: PageReviewStatus | None = Query(default=None),
    sort: str = Query(default="updated_at_desc"),
    include_data: bool = Query(default=True),
    is_template: bool | None = Query(default=None),
    origin_block_id: UUID | None = Query(default=None),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    if sort not in {"updated_at_desc", "updated_at_asc", "title_asc", "usage_desc"}:
        sort = "updated_at_desc"
    scope_filter: BlockScope | tuple[BlockScope, ...] | None
    if scope:
        unique: list[BlockScope] = []
        for item in scope:
            if item not in unique:
                unique.append(item)
        if len(unique) == 1:
            scope_filter = unique[0]
        else:
            scope_filter = tuple(unique)
    else:
        scope_filter = (BlockScope.SHARED, BlockScope.PAGE)
    blocks, total = await service.list_blocks(
        page=page,
        page_size=page_size,
        scope=scope_filter,
        section=section,
        status=status,
        locale=locale,
        query=q,
        has_draft=has_draft,
        requires_publisher=requires_publisher,
        review_status=review_status,
        sort=sort,
        is_template=is_template,
        origin_block_id=origin_block_id,
    )
    items = [_serialize_block(block) for block in blocks]
    if not include_data:
        for payload in items:
            payload.pop("data", None)
            payload.pop("meta", None)
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get(
    "/block-templates",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_block_templates(
    status_values: list[str] | None = Query(default=None, alias="status"),
    section: str | None = Query(default=None),
    q: str | None = Query(default=None),
    include_data: bool = Query(default=True),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    templates = await service.list_block_templates(
        status=status_values,
        section=section,
        query=q,
    )
    items = [_serialize_block_template(template) for template in templates]
    if not include_data:
        for payload in items:
            payload.pop("default_data", None)
            payload.pop("default_meta", None)
    return {"items": items, "total": len(items)}


@router.get(
    "/block-templates/{template_id}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_block_template(
    template_id: UUID,
    include_data: bool = Query(default=True),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        template = await service.get_block_template(template_id)
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    payload = _serialize_block_template(template)
    if not include_data:
        payload.pop("default_data", None)
        payload.pop("default_meta", None)
    return payload


@router.get(
    "/block-templates/by-key/{template_key}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_block_template_by_key(
    template_key: str,
    include_data: bool = Query(default=True),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        template = await service.get_block_template(key=template_key)
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    payload = _serialize_block_template(template)
    if not include_data:
        payload.pop("default_data", None)
        payload.pop("default_meta", None)
    return payload


@router.post(
    "/block-templates",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def create_block_template(
    request: Request,
    payload: BlockTemplateCreatePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    template = await service.create_block_template(
        key=payload.key,
        title=payload.title,
        section=payload.section,
        description=payload.description,
        status=payload.status,
        default_locale=payload.default_locale,
        available_locales=payload.available_locales,
        block_type=payload.block_type,
        category=payload.category,
        sources=payload.sources,
        surfaces=payload.surfaces,
        owners=payload.owners,
        catalog_locales=payload.catalog_locales,
        documentation_url=payload.documentation_url,
        keywords=payload.keywords,
        preview_kind=payload.preview_kind,
        status_note=payload.status_note,
        requires_publisher=payload.requires_publisher,
        allow_shared_scope=payload.allow_shared_scope,
        allow_page_scope=payload.allow_page_scope,
        shared_note=payload.shared_note,
        key_prefix=payload.key_prefix,
        default_data=payload.default_data,
        default_meta=payload.default_meta,
        actor=actor,
    )
    return _serialize_block_template(template)


@router.put(
    "/block-templates/{template_id}",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def update_block_template(
    request: Request,
    template_id: UUID,
    payload: BlockTemplateUpdatePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    try:
        template = await service.update_block_template(
            template_id,
            title=payload.title,
            section=payload.section,
            description=payload.description,
            status=payload.status,
            default_locale=payload.default_locale,
            available_locales=payload.available_locales,
            block_type=payload.block_type,
            category=payload.category,
            sources=payload.sources,
            surfaces=payload.surfaces,
            owners=payload.owners,
            catalog_locales=payload.catalog_locales,
            documentation_url=payload.documentation_url,
            keywords=payload.keywords,
            preview_kind=payload.preview_kind,
            status_note=payload.status_note,
            requires_publisher=payload.requires_publisher,
            allow_shared_scope=payload.allow_shared_scope,
            allow_page_scope=payload.allow_page_scope,
            shared_note=payload.shared_note,
            key_prefix=payload.key_prefix,
            default_data=payload.default_data,
            default_meta=payload.default_meta,
            actor=actor,
        )
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize_block_template(template)


@router.post(
    "/blocks",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def create_block(
    request: Request,
    payload: BlockCreatePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    block = await service.create_block(
        key=payload.key,
        title=payload.title,
        template_id=payload.template_id,
        template_key=payload.template_key,
        section=payload.section,
        scope=payload.scope,
        default_locale=payload.default_locale,
        available_locales=payload.available_locales,
        requires_publisher=payload.requires_publisher,
        data=payload.data,
        meta=payload.meta,
        actor=actor,
        is_template=payload.is_template,
        origin_block_id=payload.origin_block_id,
    )
    return _serialize_block(block)


@router.get(
    "/blocks/{block_id}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_block(
    block_id: UUID,
    scope: BlockScope | None = Query(default=None),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    block = await service.get_block(block_id, expected_scope=scope)
    usage = await service.list_block_usage(block_id)
    usage_payload = [_serialize_usage(item) for item in usage]
    warnings: list[dict[str, Any]] = []
    for item in usage:
        if item.has_draft:
            warnings.append(
                {
                    "code": "dependent_page_has_draft",
                    "page_id": str(item.page_id),
                    "message": f"Черновик страницы «{item.title}» не опубликован",
                }
            )
    return {
        "block": _serialize_block(block),
        "usage": usage_payload,
        "warnings": warnings,
    }


@router.put(
    "/blocks/{block_id}",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def save_block(
    request: Request,
    block_id: UUID,
    payload: BlockSavePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    try:
        block = await service.save_block(
            block_id=block_id,
            payload=payload.data,
            meta=payload.meta,
            version=payload.version,
            comment=payload.comment,
            review_status=payload.review_status,
            actor=actor,
            title=payload.title,
            section=payload.section,
            default_locale=payload.default_locale,
            available_locales=payload.available_locales,
            requires_publisher=payload.requires_publisher,
        )
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize_block(block)


@router.post(
    "/blocks/{block_id}/publish",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def publish_block(
    request: Request,
    block_id: UUID,
    payload: BlockPublishPayload = Body(default=BlockPublishPayload()),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    current_block = await service.get_block(block_id)
    usage_before = await service.list_block_usage(block_id)
    if usage_before and not payload.acknowledge_usage:
        usage_payload = [_serialize_usage(item) for item in usage_before]
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "error": "site_block_ack_required",
                "message": "Необходимо подтвердить публикацию блока со списком зависимых страниц.",
                "usage": usage_payload,
                "usage_count": len(usage_payload),
            },
        )
    if payload.version is not None and current_block.draft_version != payload.version:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="site_block_version_conflict",
        )
    published_block, audit_id, usage_after, jobs = await service.publish_block(
        block_id=block_id,
        actor=actor,
        comment=payload.comment,
        diff=payload.diff,
    )
    affected_pages = [
        {
            "page_id": str(item.page_id),
            "slug": item.slug,
            "title": item.title,
            "status": item.status.value,
            "republish_status": "queued",
        }
        for item in usage_after
    ]
    job_payload = [
        {"job_id": str(job.job_id), "type": job.type, "status": job.status.value}
        for job in jobs
    ]
    response: dict[str, Any] = {
        "id": str(published_block.id),
        "published_version": published_block.published_version,
        "affected_pages": affected_pages,
        "jobs": job_payload,
        "audit_id": str(audit_id),
        "block": _serialize_block(published_block),
        "usage": [_serialize_usage(item) for item in usage_after],
    }
    return response


@router.post(
    "/blocks/{block_id}/archive",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def archive_block(
    request: Request,
    block_id: UUID,
    payload: BlockArchivePayload = Body(default=BlockArchivePayload()),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    block, usage = await service.archive_block(
        block_id=block_id,
        actor=actor,
        restore=payload.restore,
    )
    return {
        "block": _serialize_block(block),
        "usage": [_serialize_usage(item) for item in usage],
    }


@router.get(
    "/blocks/{block_id}/history",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_block_history(
    block_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    items, total = await service.list_block_history(
        block_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize_block_version(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/blocks/{block_id}/history/{version}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_block_version(
    block_id: UUID,
    version: int,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    version_obj = await service.get_block_version(block_id, version)
    return _serialize_block_version(version_obj)


@router.get(
    "/blocks/{block_id}/metrics",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_block_metrics(
    block_id: UUID,
    period: str = Query(default="7d", pattern="^(1d|7d|30d)$"),
    locale: str = Query(default="ru", min_length=2, max_length=8),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        metrics = await service.get_block_metrics(
            block_id,
            period=period,
            locale=locale,
        )
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if metrics is None:
        return {
            "block_id": str(block_id),
            "period": period,
            "status": "no_data",
            "metrics": {},
            "alerts": [],
            "top_pages": [],
        }
    return _serialize_block_metrics(metrics)


@router.post(
    "/blocks/{block_id}/history/{version}/restore",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def restore_block_version(
    request: Request,
    block_id: UUID,
    version: int,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    block = await service.restore_block_version(block_id, version, actor=actor)
    usage = await service.list_block_usage(block_id)
    usage_payload = [_serialize_usage(item) for item in usage]
    warnings: list[dict[str, Any]] = []
    for item in usage:
        if item.has_draft:
            warnings.append(
                {
                    "code": "dependent_page_has_draft",
                    "page_id": str(item.page_id),
                    "message": f"Черновик страницы «{item.title}» не опубликован",
                }
            )
    return {
        "block": _serialize_block(block),
        "usage": usage_payload,
        "warnings": warnings,
    }


@router.get(
    "/audit",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_audit(
    entity_type: str | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    actor: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    rows, total = await service.list_audit(
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        limit=limit,
        offset=offset,
    )
    items = [
        {
            "id": str(row["id"]),
            "entity_type": row["entity_type"],
            "entity_id": str(row["entity_id"]),
            "action": row["action"],
            "snapshot": row.get("snapshot"),
            "actor": row.get("actor"),
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def make_router() -> APIRouter:
    return router


def _build_site_preview_config(
    *,
    page,
    draft,
    payload: Mapping[str, Any],
    meta: Mapping[str, Any],
) -> HomeConfig:
    now = datetime.now(UTC)
    data = deepcopy(payload)
    meta_copy = deepcopy(meta)
    if isinstance(meta_copy, Mapping):
        preview_meta = dict(meta_copy)
    else:
        preview_meta = {}
    preview_marker = preview_meta.get("preview")
    if isinstance(preview_marker, Mapping):
        preview_meta["preview"] = {**preview_marker, "mode": "site_preview"}
    else:
        preview_meta["preview"] = {"mode": "site_preview"}
    if isinstance(data, Mapping):
        data = dict(data)
    else:
        data = {}
    data["meta"] = preview_meta
    return HomeConfig(
        id=uuid4(),
        slug=page.slug,
        version=draft.version,
        status=HomeConfigStatus.DRAFT,
        data=data,
        created_by=draft.updated_by,
        updated_by=draft.updated_by,
        created_at=now,
        updated_at=now,
        published_at=None,
        draft_of=page.id,
    )
