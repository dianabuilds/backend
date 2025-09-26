from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from domains.platform.worker.application.service import (
    JobCompletionCommand,
    JobCreateCommand,
    JobFailureCommand,
    WorkerQueueService,
)
from domains.platform.worker.domain.models import JobStatus, WorkerJob


class JobPayload(BaseModel):
    job_id: UUID | None = None
    tenant_id: UUID
    type: str
    input: dict[str, Any]
    priority: int = Field(default=5, ge=0)
    idempotency_key: str | None = None
    code_version: str | None = None
    model_version: str | None = None
    config_hash: str | None = None
    cost_cap_eur: Decimal | None = None
    budget_tag: str | None = None


class JobView(BaseModel):
    job_id: UUID
    tenant_id: UUID
    type: str
    status: JobStatus
    priority: int
    idempotency_key: str | None
    code_version: str | None
    model_version: str | None
    config_hash: str | None
    lease_until: str | None
    lease_owner: str | None
    attempts: int
    cost_cap_eur: Decimal | None
    budget_tag: str | None
    input: dict[str, Any]
    result: dict[str, Any] | None
    created_at: str
    updated_at: str


class JobLeaseRequest(BaseModel):
    worker_id: str
    job_types: list[str] | None = None
    limit: int = Field(default=1, ge=1, le=100)
    lease_seconds: int = Field(default=600, ge=1, le=3600)


class JobLeaseResponse(BaseModel):
    jobs: list[JobView]


class JobHeartbeatRequest(BaseModel):
    worker_id: str
    lease_seconds: int = Field(default=600, ge=1, le=3600)


class JobCompleteRequest(BaseModel):
    worker_id: str
    result: dict[str, Any] | None = None


class JobFailRequest(BaseModel):
    worker_id: str
    error: str
    retryable: bool = False
    details: dict[str, Any] | None = None


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/worker/jobs", tags=["worker-jobs"])

    @router.post("", response_model=JobView)
    async def enqueue_job(
        payload: JobPayload,
        service: WorkerQueueService = Depends(_service_dep),
    ) -> JobView:
        job = await service.enqueue(
            JobCreateCommand(
                job_id=payload.job_id,
                tenant_id=payload.tenant_id,
                type=payload.type,
                input=payload.input,
                priority=payload.priority,
                idempotency_key=payload.idempotency_key,
                code_version=payload.code_version,
                model_version=payload.model_version,
                config_hash=payload.config_hash,
                cost_cap_eur=payload.cost_cap_eur,
                budget_tag=payload.budget_tag,
            )
        )
        return _job_to_view(job)

    @router.get("/{job_id}", response_model=JobView)
    async def get_job(
        job_id: UUID,
        service: WorkerQueueService = Depends(_service_dep),
    ) -> JobView:
        job = await service.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job_not_found")
        return _job_to_view(job)

    @router.post("/lease", response_model=JobLeaseResponse)
    async def lease_jobs(
        payload: JobLeaseRequest,
        service: WorkerQueueService = Depends(_service_dep),
    ) -> JobLeaseResponse:
        jobs = await service.lease(
            worker_id=payload.worker_id,
            job_types=payload.job_types,
            limit=payload.limit,
            lease_seconds=payload.lease_seconds,
        )
        return JobLeaseResponse(jobs=[_job_to_view(job) for job in jobs])

    @router.post("/{job_id}/heartbeat", response_model=JobView)
    async def heartbeat(
        job_id: UUID,
        payload: JobHeartbeatRequest,
        service: WorkerQueueService = Depends(_service_dep),
    ) -> JobView:
        job = await service.heartbeat(job_id, payload.worker_id, payload.lease_seconds)
        if job is None:
            raise HTTPException(status_code=404, detail="job_not_leased")
        return _job_to_view(job)

    @router.post("/{job_id}/complete", response_model=JobView)
    async def complete_job(
        job_id: UUID,
        payload: JobCompleteRequest,
        service: WorkerQueueService = Depends(_service_dep),
    ) -> JobView:
        job = await service.complete(
            JobCompletionCommand(
                job_id=job_id,
                worker_id=payload.worker_id,
                result=payload.result,
            )
        )
        return _job_to_view(job)

    @router.post("/{job_id}/fail", response_model=JobView)
    async def fail_job(
        job_id: UUID,
        payload: JobFailRequest,
        service: WorkerQueueService = Depends(_service_dep),
    ) -> JobView:
        job = await service.fail(
            JobFailureCommand(
                job_id=job_id,
                worker_id=payload.worker_id,
                error=payload.error,
                retryable=payload.retryable,
                details=payload.details,
            )
        )
        return _job_to_view(job)

    return router


def _service_dep(request: Request) -> WorkerQueueService:
    container = getattr(request.app.state, "container", None)
    if container is None or getattr(container, "worker", None) is None:
        raise RuntimeError("worker container not initialized")
    return container.worker.service  # type: ignore[no-any-return]


def _job_to_view(job: WorkerJob) -> JobView:
    lease_until = job.lease_until.isoformat() if job.lease_until else None
    created_at = job.created_at.isoformat()
    updated_at = job.updated_at.isoformat()
    return JobView(
        job_id=job.job_id,
        tenant_id=job.tenant_id,
        type=job.type,
        status=job.status,
        priority=job.priority,
        idempotency_key=job.idempotency_key,
        code_version=job.code_version,
        model_version=job.model_version,
        config_hash=job.config_hash,
        lease_until=lease_until,
        lease_owner=job.lease_owner,
        attempts=job.attempts,
        cost_cap_eur=job.cost_cap_eur,
        budget_tag=job.budget_tag,
        input=job.input,
        result=job.result,
        created_at=created_at,
        updated_at=updated_at,
    )


__all__ = ["make_router"]
