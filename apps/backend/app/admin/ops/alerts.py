from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter

router = APIRouter()


async def fetch_active_alerts() -> list[dict[str, Any]]:
    """Fetch active alerts from Prometheus if configured.

    The Prometheus base URL can be provided via the ``PROMETHEUS_URL``
    environment variable. If it's absent or the request fails, an empty
    list is returned.
    """

    base_url = os.getenv("PROMETHEUS_URL")
    if not base_url:
        return []
    url = base_url.rstrip("/") + "/api/v1/alerts"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:  # pragma: no cover - network errors
        logging.getLogger(__name__).warning(
            "Failed to fetch alerts from %s", url, exc_info=e
        )
        return []
    alerts = (
        data.get("data", {}).get("alerts")
        if isinstance(data, dict)
        else None
    )
    if isinstance(alerts, list):
        return alerts
    if isinstance(data, list):
        return data
    return []


@router.get("/alerts")
async def get_alerts() -> dict[str, list[dict[str, Any]]]:
    """Return active alerts for operational dashboard."""

    alerts = await fetch_active_alerts()
    return {"alerts": alerts}

