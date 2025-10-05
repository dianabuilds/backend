from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from packages.core.db import get_async_engine


@dataclass
class DatabaseProbe:
    database_url: str

    async def ping(self) -> tuple[float | None, str | None]:
        start = time.perf_counter()
        try:
            engine = get_async_engine("admin-db", url=self.database_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except (SQLAlchemyError, RuntimeError) as exc:
            return None, str(exc)
        return (time.perf_counter() - start) * 1000.0, None

    async def queue_stats(self) -> dict[str, Any]:
        engine = get_async_engine("admin-db", url=self.database_url)
        stats: dict[str, Any] = {
            "status": "unknown",
            "pending": None,
            "leased": None,
            "failed": None,
            "succeeded": None,
            "oldest_pending_seconds": None,
            "last_heartbeat": None,
            "error": None,
        }
        try:
            async with engine.connect() as conn:
                rows = (
                    await conn.execute(
                        text(
                            "SELECT status, COUNT(*) AS count FROM worker_jobs GROUP BY status"
                        )
                    )
                ).mappings()
                counts = {str(row["status"]).lower(): int(row["count"]) for row in rows}

            pending = counts.get("queued", 0)
            failed = counts.get("failed", 0)
            leased = counts.get("leased", 0)
            succeeded = counts.get("completed", counts.get("succeeded", 0))

            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT EXTRACT(EPOCH FROM (now() - MIN(created_at))) AS age "
                        "FROM worker_jobs WHERE status = 'queued'"
                    )
                )
                oldest_seconds = result.scalar_one_or_none()

            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT MAX(started_at) FROM worker_job_runs WHERE status = 'started'"
                    )
                )
                heartbeat = result.scalar_one_or_none()

            stats.update(
                {
                    "status": self._determine_status(pending, failed),
                    "pending": pending,
                    "leased": leased,
                    "failed": failed,
                    "succeeded": succeeded,
                    "oldest_pending_seconds": (
                        float(oldest_seconds) if oldest_seconds is not None else None
                    ),
                    "last_heartbeat": heartbeat,
                }
            )
        except SQLAlchemyError as exc:
            stats["error"] = str(exc)
        return stats

    @staticmethod
    def _determine_status(pending: int, failed: int) -> str:
        if failed > 10 or pending > 1000:
            return "critical"
        if failed > 0:
            return "warning"
        return "healthy"


__all__ = ["DatabaseProbe"]
