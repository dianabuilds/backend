from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest

from domains.platform.worker.adapters.sql.jobs import SQLWorkerJobRepository
from domains.platform.worker.application.service import (
    JobCompletionCommand,
    JobCreateCommand,
    JobFailureCommand,
    WorkerQueueService,
)
from domains.platform.worker.domain.models import JobStatus, WorkerJob


class _FakeRepo:
    def __init__(self) -> None:
        self.jobs: dict[UUID, WorkerJob] = {}
        self.idempotent: dict[tuple[str, str | None], WorkerJob] = {}

    async def enqueue(self, payload):
        job = WorkerJob(
            job_id=payload["job_id"],
            type=payload["type"],
            status=JobStatus(payload["status"]),
            priority=payload["priority"],
            idempotency_key=payload["idempotency_key"],
            code_version=payload["code_version"],
            model_version=payload["model_version"],
            config_hash=payload["config_hash"],
            lease_until=None,
            lease_owner=None,
            attempts=0,
            max_attempts=payload.get("max_attempts", 3),
            available_at=payload.get("available_at") or datetime.now(UTC),
            cost_cap_eur=payload["cost_cap_eur"],
            budget_tag=payload["budget_tag"],
            input=payload["input"],
            result=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.jobs[job.job_id] = job
        if job.idempotency_key:
            self.idempotent[(job.type, job.idempotency_key)] = job
        return job

    async def find_by_idempotency(self, job_type, key):
        return self.idempotent.get((job_type, key))

    async def lease_jobs(
        self, *, worker_id, job_types, limit, lease_seconds, job_ids=None
    ):
        now = datetime.now(UTC)
        leased = []
        ids = list(job_ids or [])
        if not ids:
            ids = [
                jid for jid, job in self.jobs.items() if job.status is JobStatus.QUEUED
            ]
        for jid in ids[:limit]:
            job = self.jobs.get(jid)
            if job and job.status is JobStatus.QUEUED and job.available_at <= now:
                leased_job = replace(
                    job,
                    status=JobStatus.LEASED,
                    lease_owner=worker_id,
                    attempts=job.attempts + 1,
                )
                self.jobs[jid] = leased_job
                leased.append(leased_job)
        return leased

    async def heartbeat(self, **kwargs):  # pragma: no cover - not used
        return None

    async def complete(self, job_id, worker_id, status, result):
        job = self.jobs[job_id]
        job = replace(job, status=JobStatus(status), result=result, lease_owner=None)
        self.jobs[job_id] = job
        return job

    async def get(self, job_id):
        return self.jobs.get(job_id)

    async def requeue_job(self, job_id, *, worker_id, available_at, priority=None):
        job = self.jobs[job_id]
        if job.lease_owner != worker_id:
            raise RuntimeError("job_not_leased_by_worker")
        new_job = replace(
            job,
            status=JobStatus.QUEUED,
            lease_owner=None,
            lease_until=None,
            available_at=available_at,
            result=None,
        )
        if priority is not None:
            new_job = replace(new_job, priority=priority)
        self.jobs[job_id] = new_job
        return new_job

    async def record_event(self, job_id, event, details=None):  # pragma: no cover
        return None


class _StubQueue:
    def __init__(self) -> None:
        self.pushed: list[tuple[UUID, int]] = []
        self.to_pop: list[UUID] = []

    async def push(self, job_id: UUID, priority: int) -> None:
        self.pushed.append((job_id, priority))

    async def pop_many(self, limit: int) -> list[UUID]:
        items = self.to_pop[:limit]
        self.to_pop = self.to_pop[len(items) :]
        return items


@pytest.mark.asyncio
async def test_enqueue_generates_job_id_when_missing() -> None:
    repo = _FakeRepo()
    service = WorkerQueueService(cast(SQLWorkerJobRepository, repo))
    job = await service.enqueue(JobCreateCommand(type="test", input={"foo": "bar"}))
    assert job.job_id in repo.jobs
    assert job.input == {"foo": "bar"}


@pytest.mark.asyncio
async def test_enqueue_returns_existing_for_idempotent_key() -> None:
    repo = _FakeRepo()
    service = WorkerQueueService(cast(SQLWorkerJobRepository, repo))
    first = await service.enqueue(
        JobCreateCommand(
            type="test",
            input={"foo": 1},
            idempotency_key="abc",
        )
    )
    second = await service.enqueue(
        JobCreateCommand(
            type="test",
            input={"foo": 2},
            idempotency_key="abc",
        )
    )
    assert first.job_id == second.job_id
    assert second.input == {"foo": 1}


@pytest.mark.asyncio
async def test_enqueue_pushes_to_queue() -> None:
    repo = _FakeRepo()
    queue = _StubQueue()
    service = WorkerQueueService(cast(SQLWorkerJobRepository, repo), queue=queue)
    job = await service.enqueue(JobCreateCommand(type="test", input={}, priority=2))
    assert queue.pushed == [(job.job_id, 2)]


@pytest.mark.asyncio
async def test_complete_updates_status() -> None:
    repo = _FakeRepo()
    service = WorkerQueueService(cast(SQLWorkerJobRepository, repo))
    job = await service.enqueue(JobCreateCommand(type="test", input={}))
    completed = await service.complete(
        JobCompletionCommand(
            job_id=job.job_id, worker_id="worker-1", result={"ok": True}
        )
    )
    assert completed.status is JobStatus.SUCCEEDED
    assert completed.result == {"ok": True}


@pytest.mark.asyncio
async def test_fail_requeues_when_retryable() -> None:
    repo = _FakeRepo()
    queue = _StubQueue()
    service = WorkerQueueService(cast(SQLWorkerJobRepository, repo), queue=queue)
    job = await service.enqueue(JobCreateCommand(type="test", input={}))
    repo.jobs[job.job_id] = replace(
        repo.jobs[job.job_id],
        attempts=1,
        status=JobStatus.LEASED,
        lease_owner="worker-1",
    )
    before_pushes = len(queue.pushed)
    failed = await service.fail(
        JobFailureCommand(
            job_id=job.job_id,
            worker_id="worker-1",
            error="network",
            retryable=True,
        )
    )
    assert failed.status is JobStatus.QUEUED
    assert len(queue.pushed) == before_pushes + 1
    assert queue.pushed[-1][0] == job.job_id
    assert repo.jobs[job.job_id].available_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_fail_final_when_attempts_exhausted() -> None:
    repo = _FakeRepo()
    queue = _StubQueue()
    service = WorkerQueueService(cast(SQLWorkerJobRepository, repo), queue=queue)
    job = await service.enqueue(JobCreateCommand(type="test", input={}, priority=1))
    repo.jobs[job.job_id] = replace(
        repo.jobs[job.job_id],
        attempts=3,
        max_attempts=3,
        status=JobStatus.LEASED,
        lease_owner="worker-1",
    )
    before_pushes = len(queue.pushed)
    result = await service.fail(
        JobFailureCommand(
            job_id=job.job_id,
            worker_id="worker-1",
            error="boom",
            retryable=True,
        )
    )
    assert result.status is JobStatus.FAILED
    assert len(queue.pushed) == before_pushes
