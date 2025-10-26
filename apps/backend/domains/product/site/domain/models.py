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
    locale: str
    owner: str | None
    created_at: datetime
    updated_at: datetime
    published_version: int | None = None
    draft_version: int | None = None
    has_pending_review: bool = False


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


class GlobalBlockStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass(slots=True)
class GlobalBlock:
    id: UUID
    key: str
    title: str
    section: str
    locale: str | None
    status: GlobalBlockStatus
    review_status: PageReviewStatus
    data: Mapping[str, Any]
    meta: Mapping[str, Any]
    updated_at: datetime
    updated_by: str | None
    requires_publisher: bool
    published_version: int | None = None
    draft_version: int | None = None
    comment: str | None = None
    usage_count: int | None = None


@dataclass(slots=True)
class GlobalBlockDraft:
    block_id: UUID
    version: int
    data: Mapping[str, Any]
    meta: Mapping[str, Any]
    comment: str | None
    review_status: PageReviewStatus
    updated_at: datetime
    updated_by: str | None


@dataclass(slots=True)
class GlobalBlockVersion:
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
class GlobalBlockUsage:
    block_id: UUID
    page_id: UUID
    slug: str
    title: str
    status: PageStatus
    section: str
    locale: str | None = None
    has_draft: bool | None = None
    last_published_at: datetime | None = None


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
class BlockTopPage:
    page_id: UUID
    slug: str
    title: str
    impressions: int | None = None
    clicks: int | None = None
    ctr: float | None = None


@dataclass(slots=True)
class GlobalBlockMetrics:
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
    "GlobalBlock",
    "GlobalBlockDraft",
    "GlobalBlockStatus",
    "GlobalBlockVersion",
    "GlobalBlockUsage",
    "GlobalBlockMetrics",
    "BlockTopPage",
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
