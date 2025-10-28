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
from pydantic import BaseModel, Field

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
    BlockTopPage,
    GlobalBlockMetrics,
    GlobalBlockStatus,
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


def _serialize_page(page) -> dict[str, Any]:
    return {
        "id": str(page.id),
        "slug": page.slug,
        "type": page.type.value,
        "status": page.status.value,
        "title": page.title,
        "locale": page.locale,
        "owner": page.owner,
        "created_at": page.created_at.isoformat(),
        "updated_at": page.updated_at.isoformat(),
        "published_version": page.published_version,
        "draft_version": page.draft_version,
        "has_pending_review": page.has_pending_review,
        "pinned": page.pinned,
    }


def _serialize_draft(draft) -> dict[str, Any]:
    return {
        "page_id": str(draft.page_id),
        "version": draft.version,
        "data": draft.data,
        "meta": draft.meta,
        "comment": draft.comment,
        "review_status": draft.review_status.value,
        "updated_at": draft.updated_at.isoformat(),
        "updated_by": draft.updated_by,
        "global_blocks": repo_helpers.format_global_block_refs(draft.data, draft.meta),
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
        "global_blocks": repo_helpers.format_global_block_refs(
            version.data, version.meta
        ),
    }


def _serialize_page_global_blocks(
    blocks: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for block in blocks:
        item = {
            "block_id": block.get("block_id"),
            "key": block.get("key"),
            "title": block.get("title"),
            "section": block.get("section"),
            "status": block.get("status"),
            "locale": block.get("locale"),
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


def _serialize_block(block) -> dict[str, Any]:
    return {
        "id": str(block.id),
        "key": block.key,
        "title": block.title,
        "section": block.section,
        "locale": block.locale,
        "status": block.status.value,
        "review_status": block.review_status.value,
        "data": block.data,
        "meta": block.meta,
        "updated_at": block.updated_at.isoformat(),
        "updated_by": block.updated_by,
        "published_version": block.published_version,
        "draft_version": block.draft_version,
        "requires_publisher": block.requires_publisher,
        "comment": block.comment,
        "usage_count": int(block.usage_count or 0),
        "has_pending_publish": (block.draft_version or 0)
        > (block.published_version or 0),
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


def _serialize_block_metrics(metrics: GlobalBlockMetrics) -> dict[str, Any]:
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


class GlobalBlockSavePayload(BaseModel):
    version: int | None = Field(default=None, ge=0)
    data: Mapping[str, Any] = Field(default_factory=dict)
    meta: Mapping[str, Any] = Field(default_factory=dict)
    comment: str | None = Field(default=None, max_length=500)
    review_status: PageReviewStatus = Field(default=PageReviewStatus.NONE)


class GlobalBlockCreatePayload(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    section: str = Field(default="promo", min_length=1, max_length=64)
    locale: str | None = Field(default=None, max_length=10)
    requires_publisher: bool = Field(default=False)
    data: Mapping[str, Any] = Field(default_factory=dict)
    meta: Mapping[str, Any] = Field(default_factory=dict)


class GlobalBlockPublishPayload(BaseModel):
    comment: str | None = Field(default=None, max_length=500)
    diff: list[Mapping[str, Any]] | None = None
    version: int | None = Field(default=None, ge=0)
    acknowledge_usage: bool = Field(default=False)


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
    payload = _serialize_page(page)
    payload["global_blocks"] = _serialize_page_global_blocks(blocks)
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
    return _serialize_draft(draft)


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
    "/global-blocks",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_global_blocks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    section: str | None = Query(default=None),
    status: GlobalBlockStatus | None = Query(default=None),
    locale: str | None = Query(default=None),
    q: str | None = Query(default=None),
    has_draft: bool | None = Query(default=None),
    requires_publisher: bool | None = Query(default=None),
    review_status: PageReviewStatus | None = Query(default=None),
    sort: str = Query(default="updated_at_desc"),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    if sort not in {"updated_at_desc", "updated_at_asc", "title_asc", "usage_desc"}:
        sort = "updated_at_desc"
    blocks, total = await service.list_global_blocks(
        page=page,
        page_size=page_size,
        section=section,
        status=status,
        locale=locale,
        query=q,
        has_draft=has_draft,
        requires_publisher=requires_publisher,
        review_status=review_status,
        sort=sort,
    )
    return {
        "items": [_serialize_block(block) for block in blocks],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post(
    "/global-blocks",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def create_global_block(
    request: Request,
    payload: GlobalBlockCreatePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    block = await service.create_global_block(
        key=payload.key,
        title=payload.title,
        section=payload.section,
        locale=payload.locale,
        requires_publisher=payload.requires_publisher,
        data=payload.data,
        meta=payload.meta,
        actor=actor,
    )
    return _serialize_block(block)


@router.get(
    "/global-blocks/{block_id}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_global_block(
    block_id: UUID,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    block = await service.get_global_block(block_id)
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
    "/global-blocks/{block_id}",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def save_global_block(
    request: Request,
    block_id: UUID,
    payload: GlobalBlockSavePayload = Body(...),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    try:
        block = await service.save_global_block(
            block_id=block_id,
            payload=payload.data,
            meta=payload.meta,
            version=payload.version,
            comment=payload.comment,
            review_status=payload.review_status,
            actor=actor,
        )
    except SiteRepositoryError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize_block(block)


@router.post(
    "/global-blocks/{block_id}/publish",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def publish_global_block(
    request: Request,
    block_id: UUID,
    payload: GlobalBlockPublishPayload = Body(default=GlobalBlockPublishPayload()),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    current_block = await service.get_global_block(block_id)
    usage_before = await service.list_block_usage(block_id)
    if usage_before and not payload.acknowledge_usage:
        usage_payload = [_serialize_usage(item) for item in usage_before]
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "error": "site_global_block_ack_required",
                "message": "Необходимо подтвердить публикацию глобального блока со списком зависимых страниц.",
                "usage": usage_payload,
                "usage_count": len(usage_payload),
            },
        )
    if payload.version is not None and current_block.draft_version != payload.version:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="site_global_block_version_conflict",
        )
    published_block, audit_id, usage_after, jobs = await service.publish_global_block(
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


@router.get(
    "/global-blocks/{block_id}/history",
    dependencies=[Depends(require_role_db("user"))],
)
async def list_global_block_history(
    block_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    items, total = await service.list_global_block_history(
        block_id, limit=limit, offset=offset
    )
    return {
        "items": [_serialize_block_version(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/global-blocks/{block_id}/history/{version}",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_global_block_version(
    block_id: UUID,
    version: int,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    version_obj = await service.get_global_block_version(block_id, version)
    return _serialize_block_version(version_obj)


@router.get(
    "/global-blocks/{block_id}/metrics",
    dependencies=[Depends(require_role_db("user"))],
)
async def get_global_block_metrics(
    block_id: UUID,
    period: str = Query(default="7d", pattern="^(1d|7d|30d)$"),
    locale: str = Query(default="ru", min_length=2, max_length=8),
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    try:
        metrics = await service.get_global_block_metrics(
            block_id, period=period, locale=locale
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
    "/global-blocks/{block_id}/history/{version}/restore",
    dependencies=[Depends(csrf_protect), Depends(require_role_db("editor"))],
)
async def restore_global_block_version(
    request: Request,
    block_id: UUID,
    version: int,
    service: SiteService = Depends(get_site_service),
) -> dict[str, Any]:
    user = await get_current_user(request)
    actor = user.get("email") or user.get("id")
    block = await service.restore_global_block_version(block_id, version, actor=actor)
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
