from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.worker.domain.models import JobStatus, WorkerJob
from packages.core.db import get_async_engine


class SQLWorkerJobRepository:
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, AsyncEngine):
            self._engine = engine
        else:
            self._engine = get_async_engine("worker", url=engine)

    async def enqueue(self, payload: dict[str, Any]) -> WorkerJob:
        sql = text(
            """
            INSERT INTO worker_jobs (
                job_id,
                type,
                status,
                priority,
                idempotency_key,
                code_version,
                model_version,
                config_hash,
                attempts,
                cost_cap_eur,
                budget_tag,
                input,
                result
            ) VALUES (
                :job_id,
                :type,
                :status,
                :priority,
                :idempotency_key,
                :code_version,
                :model_version,
                :config_hash,
                0,
                :cost_cap_eur,
                :budget_tag,
                :input,
                NULL
            )
            RETURNING *
            """
        )
        try:
            async with self._engine.begin() as conn:
                row = (await conn.execute(sql, payload)).mappings().first()
                if row is None:

                    raise RuntimeError("database_row_missing")
                await conn.execute(
                    text(
                        "INSERT INTO worker_job_events (job_id, event, details) VALUES (:job_id, :event, :details)"
                    ),
                    {
                        "job_id": row["job_id"],
                        "event": "queued",
                        "details": {"priority": row["priority"]},
                    },
                )
                return self._row_to_job(row)
        except IntegrityError:
            existing = await self.find_by_idempotency(
                payload["type"], payload.get("idempotency_key")
            )
            if existing is None:
                raise
            return existing

    async def get(self, job_id: UUID) -> WorkerJob | None:
        sql = text("SELECT * FROM worker_jobs WHERE job_id = :job_id")
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"job_id": job_id})).mappings().first()
        return self._row_to_job(row) if row else None

    async def find_by_idempotency(
        self, job_type: str, key: str | None
    ) -> WorkerJob | None:
        sql = text(
            "SELECT * FROM worker_jobs WHERE type = :type AND idempotency_key = :key"
        )
        async with self._engine.begin() as conn:
            row = (
                (await conn.execute(sql, {"type": job_type, "key": key}))
                .mappings()
                .first()
            )
        return self._row_to_job(row) if row else None

    async def lease_jobs(
        self,
        *,
        worker_id: str,
        job_types: Sequence[str] | None,
        limit: int,
        lease_seconds: int,
        job_ids: Sequence[UUID] | None = None,
    ) -> list[WorkerJob]:
        if limit <= 0:
            return []
        now = datetime.now(UTC)
        lease_until = now + timedelta(seconds=max(lease_seconds, 1))

        selected_ids: list[UUID] = []
        select_sql = None
        select_params: dict[str, Any] = {}
        if job_ids:
            selected_ids = list(job_ids)[:limit]
            if not selected_ids:
                return []
        elif job_types:
            select_sql = text(
                """
                SELECT job_id
                FROM worker_jobs
                WHERE status = 'queued' AND type = ANY(:types) AND available_at <= :now
                ORDER BY priority ASC, available_at ASC, created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT :limit
            """
            )
            select_params = {"types": list(job_types), "limit": limit, "now": now}
        else:
            select_sql = text(
                """
                SELECT job_id
                FROM worker_jobs
                WHERE status = 'queued' AND available_at <= :now
                ORDER BY priority ASC, available_at ASC, created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT :limit
            """
            )
            select_params = {"limit": limit, "now": now}

        update_sql = text(
            """
            UPDATE worker_jobs
            SET status = :status,
                lease_owner = :worker_id,
                lease_until = :lease_until,
                attempts = attempts + 1,
                updated_at = now()
            WHERE job_id = ANY(:ids)
              AND status = 'queued'
              AND available_at <= :now
            RETURNING *
        """
        )

        jobs: list[WorkerJob] = []
        async with self._engine.begin() as conn:
            if not job_ids:
                if select_sql is None:

                    raise RuntimeError("lease_jobs_filter_missing")
                raw_ids = (
                    (await conn.execute(select_sql, select_params)).scalars().all()
                )
                selected_ids = [
                    value if isinstance(value, UUID) else UUID(str(value))
                    for value in raw_ids
                ]
                if not selected_ids:
                    return []
            rows = (
                (
                    await conn.execute(
                        update_sql,
                        {
                            "status": JobStatus.LEASED.value,
                            "worker_id": worker_id,
                            "lease_until": lease_until,
                            "ids": selected_ids,
                            "now": now,
                        },
                    )
                )
                .mappings()
                .all()
            )
            for row in rows:
                job = self._row_to_job(row)
                jobs.append(job)
                await conn.execute(
                    text(
                        "INSERT INTO worker_job_events (job_id, event, details) VALUES (:job_id, :event, :details)"
                    ),
                    {
                        "job_id": job.job_id,
                        "event": "leased",
                        "details": {
                            "worker_id": worker_id,
                            "lease_until": lease_until.isoformat(),
                        },
                    },
                )
        return jobs

    async def heartbeat(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        lease_seconds: int,
    ) -> WorkerJob | None:
        lease_until = datetime.now(UTC) + timedelta(seconds=max(lease_seconds, 1))
        sql = text(
            """
            UPDATE worker_jobs
            SET lease_until = :lease_until,
                updated_at = now()
            WHERE job_id = :job_id
              AND lease_owner = :worker_id
              AND status = :status
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        sql,
                        {
                            "job_id": job_id,
                            "worker_id": worker_id,
                            "lease_until": lease_until,
                            "status": JobStatus.LEASED.value,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if row:
                await conn.execute(
                    text(
                        "INSERT INTO worker_job_events (job_id, event, details) VALUES (:job_id, :event, :details)"
                    ),
                    {
                        "job_id": job_id,
                        "event": "heartbeat",
                        "details": {"lease_until": lease_until.isoformat()},
                    },
                )
        return self._row_to_job(row) if row else None

    async def complete(
        self,
        *,
        job_id: UUID,
        worker_id: str,
        status: JobStatus,
        result: dict[str, Any] | None,
    ) -> WorkerJob:
        if status not in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELED}:
            raise ValueError("invalid completion status")
        sql = text(
            """
            UPDATE worker_jobs
            SET status = :status,
                result = :result,
                lease_owner = NULL,
                lease_until = NULL,
                updated_at = now()
            WHERE job_id = :job_id AND lease_owner = :worker_id
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        sql,
                        {
                            "job_id": job_id,
                            "worker_id": worker_id,
                            "status": status.value,
                            "result": result,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise RuntimeError("job_not_leased_by_worker")
            await conn.execute(
                text(
                    "INSERT INTO worker_job_events (job_id, event, details) VALUES (:job_id, :event, :details)"
                ),
                {
                    "job_id": job_id,
                    "event": status.value,
                    "details": result or {},
                },
            )
            return self._row_to_job(row)

    async def requeue_job(
        self,
        job_id: UUID,
        *,
        worker_id: str,
        available_at: datetime,
        priority: int | None = None,
    ) -> WorkerJob:
        sql = text(
            """
            UPDATE worker_jobs
            SET status = :status,
                lease_owner = NULL,
                lease_until = NULL,
                available_at = :available_at,
                priority = COALESCE(:priority, priority),
                result = NULL,
                updated_at = now()
            WHERE job_id = :job_id AND lease_owner = :worker_id
            RETURNING *
            """
        )
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        sql,
                        {
                            "job_id": job_id,
                            "worker_id": worker_id,
                            "status": JobStatus.QUEUED.value,
                            "available_at": available_at,
                            "priority": priority,
                        },
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise RuntimeError("job_not_leased_by_worker")
            job = self._row_to_job(row)
            await conn.execute(
                text(
                    "INSERT INTO worker_job_events (job_id, event, details) VALUES (:job_id, :event, :details)"
                ),
                {
                    "job_id": job.job_id,
                    "event": "requeued",
                    "details": {
                        "available_at": available_at.isoformat(),
                        "priority": job.priority,
                        "worker_id": worker_id,
                    },
                },
            )
            return job

    async def record_event(
        self,
        job_id: UUID,
        event: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        sql = text(
            "INSERT INTO worker_job_events (job_id, event, details) VALUES (:job_id, :event, :details)"
        )
        async with self._engine.begin() as conn:
            await conn.execute(
                sql, {"job_id": job_id, "event": event, "details": details}
            )

    def _row_to_job(self, row: Any) -> WorkerJob:
        if row is None:
            raise RuntimeError("job_row_required")
        cost_cap = row.get("cost_cap_eur")
        if cost_cap is not None and not isinstance(cost_cap, Decimal):
            cost_cap = Decimal(str(cost_cap))
        input_payload = self._ensure_dict(row.get("input")) or {}
        result_payload = self._ensure_dict(row.get("result"))
        return WorkerJob(
            job_id=row["job_id"],
            type=row["type"],
            status=JobStatus(row["status"]),
            priority=int(row["priority"]),
            idempotency_key=row.get("idempotency_key"),
            code_version=row.get("code_version"),
            model_version=row.get("model_version"),
            config_hash=row.get("config_hash"),
            lease_until=row.get("lease_until"),
            lease_owner=row.get("lease_owner"),
            attempts=int(row.get("attempts", 0)),
            max_attempts=int(row.get("max_attempts", 3)),
            available_at=row.get("available_at"),
            cost_cap_eur=cost_cap,
            budget_tag=row.get("budget_tag"),
            input=input_payload,
            result=result_payload,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _ensure_dict(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if hasattr(value, "items"):
            return dict(value.items())
        raise ValueError("expected mapping payload")


__all__ = ["SQLWorkerJobRepository"]
