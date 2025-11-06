from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class PageType(str, Enum):
    LANDING = "landing"
    COLLECTION = "collection"
    ARTICLE = "article"
    SYSTEM = "system"


class PageStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PageReviewStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MetricSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(slots=True)
class MetricValue:
    value: float | int | None
    delta: float | None = None
    unit: str | None = None
    trend: tuple[float, ...] | None = None


@dataclass(slots=True)
class MetricAlert:
    code: str
    message: str
    severity: MetricSeverity = MetricSeverity.INFO


@dataclass(slots=True)
class Page:
    id: UUID
    slug: str
    type: PageType
    status: PageStatus
    title: str
    default_locale: str
    owner: str | None
    created_at: datetime
    updated_at: datetime
    published_version: int | None = None
    draft_version: int | None = None
    has_pending_review: bool = False
    pinned: bool = False
    available_locales: tuple[str, ...] = field(default_factory=tuple)
    slug_localized: Mapping[str, str] | None = None
    locale: str | None = None


@dataclass(slots=True)
class PageDraft:
    page_id: UUID
    version: int
    data: Mapping[str, Any]
    meta: Mapping[str, Any]
    updated_at: datetime
    updated_by: str | None
    comment: str | None = None
    review_status: PageReviewStatus = PageReviewStatus.NONE


@dataclass(slots=True)
class PageVersion:
    id: UUID
    page_id: UUID
    version: int
    data: Mapping[str, Any]
    meta: Mapping[str, Any]
    published_at: datetime
    published_by: str | None
    comment: str | None = None
    diff: list[Mapping[str, Any]] | None = None


class BlockScope(str, Enum):
    PAGE = "page"
    SHARED = "shared"


class BlockStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass(slots=True)
class Block:
    id: UUID
    key: str | None
    title: str | None
    section: str
    updated_at: datetime
    template_id: UUID | None = None
    template_key: str | None = None
    updated_by: str | None = None
    scope: BlockScope = BlockScope.SHARED
    default_locale: str = "ru"
    available_locales: tuple[str, ...] = field(default_factory=tuple)
    status: BlockStatus = BlockStatus.DRAFT
    review_status: PageReviewStatus = PageReviewStatus.NONE
    data: Mapping[str, Any] = field(default_factory=dict)
    meta: Mapping[str, Any] = field(default_factory=dict)
    requires_publisher: bool = False
    published_version: int | None = None
    draft_version: int | None = None
    comment: str | None = None
    usage_count: int | None = None
    extras: Mapping[str, Any] | None = None
    locale: str | None = None
    created_at: datetime | None = None
    updated_by_id: str | None = None
    version: int | None = None
    has_pending_publish: bool | None = None
    source: str | None = None
    is_template: bool = False
    origin_block_id: UUID | None = None


@dataclass(slots=True)
class BlockDraft:
    block_id: UUID
    version: int
    data: Mapping[str, Any]
    meta: Mapping[str, Any]
    comment: str | None
    review_status: PageReviewStatus
    updated_at: datetime
    updated_by: str | None


@dataclass(slots=True)
class BlockVersion:
    id: UUID
    block_id: UUID
    version: int
    data: Mapping[str, Any]
    meta: Mapping[str, Any]
    comment: str | None
    diff: list[Mapping[str, Any]] | None
    published_at: datetime
    published_by: str | None


@dataclass(slots=True)
class BlockBinding:
    block_id: UUID
    page_id: UUID
    section: str
    locale: str
    has_draft: bool | None = None
    last_published_at: datetime | None = None
    active: bool | None = None
    position: int | None = None
    title: str | None = None
    key: str | None = None
    slug: str | None = None
    page_status: PageStatus | None = None
    owner: str | None = None
    default_locale: str | None = None
    available_locales: tuple[str, ...] | None = None
    scope: BlockScope | None = None
    requires_publisher: bool | None = None
    status: BlockStatus | None = None
    review_status: PageReviewStatus | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None
    extras: Mapping[str, Any] | None = None


@dataclass(slots=True)
class BlockUsage:
    block_id: UUID
    page_id: UUID
    slug: str
    title: str
    status: PageStatus
    section: str
    locale: str | None = None
    has_draft: bool | None = None
    last_published_at: datetime | None = None
    owner: str | None = None


@dataclass(slots=True)
class BlockTemplate:
    id: UUID
    key: str
    title: str
    section: str
    default_locale: str = "ru"
    description: str | None = None
    status: str = "available"
    available_locales: tuple[str, ...] = field(default_factory=tuple)
    default_data: Mapping[str, Any] = field(default_factory=dict)
    default_meta: Mapping[str, Any] = field(default_factory=dict)
    block_type: str | None = None
    category: str | None = None
    sources: tuple[str, ...] = field(default_factory=tuple)
    surfaces: tuple[str, ...] = field(default_factory=tuple)
    owners: tuple[str, ...] = field(default_factory=tuple)
    catalog_locales: tuple[str, ...] = field(default_factory=tuple)
    documentation_url: str | None = None
    keywords: tuple[str, ...] = field(default_factory=tuple)
    preview_kind: str | None = None
    status_note: str | None = None
    requires_publisher: bool = False
    allow_shared_scope: bool = True
    allow_page_scope: bool = True
    shared_note: str | None = None
    key_prefix: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None


@dataclass(slots=True)
class BlockTopPage:
    page_id: UUID
    slug: str
    title: str
    impressions: int | None = None
    clicks: int | None = None
    ctr: float | None = None


@dataclass(slots=True)
class PageMetrics:
    page_id: UUID
    period: str
    range_start: datetime
    range_end: datetime
    status: str
    source_lag_ms: int | None
    metrics: Mapping[str, MetricValue]
    alerts: list[MetricAlert] = field(default_factory=list)
    previous_range_start: datetime | None = None
    previous_range_end: datetime | None = None


@dataclass(slots=True)
class BlockMetrics:
    block_id: UUID
    period: str
    range_start: datetime
    range_end: datetime
    status: str
    source_lag_ms: int | None
    metrics: Mapping[str, MetricValue]
    top_pages: list[BlockTopPage] = field(default_factory=list)
    alerts: list[MetricAlert] = field(default_factory=list)
    previous_range_start: datetime | None = None
    previous_range_end: datetime | None = None


__all__ = [
    "BlockScope",
    "BlockStatus",
    "Block",
    "BlockDraft",
    "BlockVersion",
    "BlockBinding",
    "BlockMetrics",
    "BlockTopPage",
    "BlockUsage",
    "MetricAlert",
    "MetricSeverity",
    "MetricValue",
    "Page",
    "PageDraft",
    "PageReviewStatus",
    "PageStatus",
    "PageType",
    "PageVersion",
    "PageMetrics",
]
