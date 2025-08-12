from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.core.metrics import metrics_storage


router = APIRouter(
    prefix="/admin/metrics",
    tags=["admin"],
    dependencies=[Depends(require_admin_role())],
    responses=ADMIN_AUTH_RESPONSES,
)


class MetricsSummary(BaseModel):
    rps: float
    error_rate: float
    p95_latency: float
    count_429: int


_RANGE_MAP = {"1h": 3600, "24h": 24 * 3600}


def _parse_range(range_str: str) -> int:
    return _RANGE_MAP.get(range_str, 3600)


@router.get("/summary", response_model=MetricsSummary)
async def metrics_summary(range: str = Query("1h")) -> MetricsSummary:  # noqa: A002
    seconds = _parse_range(range)
    summary = metrics_storage.summary(seconds)
    return MetricsSummary(**summary)
