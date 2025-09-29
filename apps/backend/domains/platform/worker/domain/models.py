from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


class JobStatus(str, Enum):
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    EXPIRED = "expired"


@dataclass(slots=True)
class WorkerJob:
    job_id: UUID
    type: str
    status: JobStatus
    priority: int
    idempotency_key: str | None
    code_version: str | None
    model_version: str | None
    config_hash: str | None
    lease_until: datetime | None
    lease_owner: str | None
    attempts: int
    max_attempts: int
    available_at: datetime
    cost_cap_eur: Decimal | None
    budget_tag: str | None
    input: dict[str, Any]
    result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class WorkerJobEvent:
    id: int
    job_id: UUID
    ts: datetime
    event: str
    details: dict[str, Any] | None


__all__ = ["JobStatus", "WorkerJob", "WorkerJobEvent"]
