from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from domains.platform.worker.domain.models import JobStatus, WorkerJob

from ..adapters.sql.jobs import SQLWorkerJobRepository


@dataclass(slots=True)
class JobCreateCommand:
    type: str
    input: dict[str, Any]
    priority: int = 5
    idempotency_key: str | None = None
    code_version: str | None = None
    model_version: str | None = None
    config_hash: str | None = None
    cost_cap_eur: Decimal | None = None
    budget_tag: str | None = None
    job_id: UUID | None = None


@dataclass(slots=True)
class JobCompletionCommand:
    job_id: UUID
    worker_id: str
    result: dict[str, Any] | None = None


@dataclass(slots=True)
class JobFailureCommand:
    job_id: UUID
    worker_id: str
    error: str
    retryable: bool = False
    details: dict[str, Any] | None = None


class WorkerQueueService:
    def __init__(self, repo: SQLWorkerJobRepository, queue=None) -> None:
        self._repo = repo
        self._queue = queue

    async def enqueue(self, command: JobCreateCommand) -> WorkerJob:
        if command.job_id is None:
            job_id = uuid4()
        else:
            job_id = command.job_id
        if command.idempotency_key:
            existing = await self._repo.find_by_idempotency(
                command.type, command.idempotency_key
            )
            if existing is not None:
                return existing
        input_payload: Any = command.input
        if input_payload is not None and not isinstance(input_payload, str):
            try:
                import json

                input_payload = json.dumps(input_payload)
            except TypeError as exc:
                raise ValueError("worker_job_input_not_serializable") from exc
        payload = {
            "job_id": job_id,
            "type": command.type,
            "status": JobStatus.QUEUED.value,
            "priority": command.priority,
            "idempotency_key": command.idempotency_key,
            "code_version": command.code_version,
            "model_version": command.model_version,
            "config_hash": command.config_hash,
            "cost_cap_eur": command.cost_cap_eur,
            "budget_tag": command.budget_tag,
            "input": input_payload,
        }
        job = await self._repo.enqueue(payload)
        if self._queue is not None:
            await self._queue.push(job.job_id, job.priority)
        return job

    async def lease(
        self,
        *,
        worker_id: str,
        job_types: Sequence[str] | None,
        limit: int,
        lease_seconds: int,
    ) -> list[WorkerJob]:
        if self._queue is not None and not job_types:
            ids = await self._queue.pop_many(limit)
            jobs: list[WorkerJob] = []
            if ids:
                leased = await self._repo.lease_jobs(
                    worker_id=worker_id,
                    job_types=None,
                    limit=len(ids),
                    lease_seconds=lease_seconds,
                    job_ids=ids,
                )
                jobs.extend(leased)
                leased_ids = {job.job_id for job in leased}
                missing = [jid for jid in ids if jid not in leased_ids]
                for jid in missing:
                    existing = await self._repo.get(jid)
                    if existing and existing.status is JobStatus.QUEUED:
                        await self._queue.push(existing.job_id, existing.priority)
            remaining = limit - len(jobs)
            if remaining > 0:
                extra = await self._repo.lease_jobs(
                    worker_id=worker_id,
                    job_types=job_types,
                    limit=remaining,
                    lease_seconds=lease_seconds,
                )
                jobs.extend(extra)
            return jobs
        return await self._repo.lease_jobs(
            worker_id=worker_id,
            job_types=job_types,
            limit=limit,
            lease_seconds=lease_seconds,
        )

    async def heartbeat(
        self, job_id: UUID, worker_id: str, lease_seconds: int
    ) -> WorkerJob | None:
        return await self._repo.heartbeat(
            job_id=job_id,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

    async def complete(self, command: JobCompletionCommand) -> WorkerJob:
        return await self._repo.complete(
            job_id=command.job_id,
            worker_id=command.worker_id,
            status=JobStatus.SUCCEEDED,
            result=command.result,
        )

    async def fail(self, command: JobFailureCommand) -> WorkerJob:
        details = dict(command.details or {})
        details.setdefault("error", command.error)
        details.setdefault("retryable", command.retryable)

        job = await self._repo.get(command.job_id)
        if job is None:
            raise RuntimeError("job_not_found")
        if job.lease_owner != command.worker_id:
            raise RuntimeError("job_not_leased_by_worker")
        if job.status is not JobStatus.LEASED:
            raise RuntimeError("job_not_leased")

        should_retry = command.retryable and job.attempts < job.max_attempts
        if should_retry:
            retry_details = dict(details)
            retry_details.setdefault("attempt", job.attempts)
            retry_details.setdefault("max_attempts", job.max_attempts)
            delay = self._retry_delay(job.attempts)
            retry_details.setdefault("retry_in_seconds", int(delay.total_seconds()))
            await self._repo.record_event(job.job_id, "failed", retry_details)
            next_available = datetime.now(UTC) + delay
            job = await self._repo.requeue_job(
                job.job_id,
                worker_id=command.worker_id,
                available_at=next_available,
            )
            if self._queue is not None:
                await self._queue.push(job.job_id, job.priority)
            return job

        failure_details = dict(details)
        failure_details.setdefault("attempt", job.attempts)
        return await self._repo.complete(
            job_id=command.job_id,
            worker_id=command.worker_id,
            status=JobStatus.FAILED,
            result=failure_details,
        )

    @staticmethod
    def _retry_delay(attempts: int) -> timedelta:
        base = 30
        exponent = max(attempts - 1, 0)
        seconds = base * (2**exponent)
        seconds = max(5, min(seconds, 1800))
        return timedelta(seconds=seconds)

    async def mark_canceled(self, job_id: UUID, worker_id: str) -> WorkerJob:
        return await self._repo.complete(
            job_id=job_id,
            worker_id=worker_id,
            status=JobStatus.CANCELED,
            result=None,
        )

    async def get(self, job_id: UUID) -> WorkerJob | None:
        return await self._repo.get(job_id)


__all__ = [
    "JobCreateCommand",
    "JobCompletionCommand",
    "JobFailureCommand",
    "WorkerQueueService",
]
