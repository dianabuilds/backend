from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/jobs")


@router.get("/")
async def list_jobs() -> dict[str, object]:
    """List recent background jobs."""
    return {"jobs": []}


@router.post("/{job_id}/retry")
async def retry_job(job_id: str) -> dict[str, str]:
    """Retry a failed job."""
    return {"job_id": job_id, "status": "retried"}
