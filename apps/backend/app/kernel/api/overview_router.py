from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()

_start_time = datetime.now(UTC)


@router.get("/overview")
async def get_overview() -> dict[str, object]:
    """Return basic operational metrics."""
    uptime = (datetime.now(UTC) - _start_time).total_seconds()
    return {
        "uptime": uptime,
        "latency": {"p95": 0.0, "p99": 0.0},
        "rq": {"queued": 0, "failed": 0},
        "postgres": "ok",
        "redis": "ok",
    }

