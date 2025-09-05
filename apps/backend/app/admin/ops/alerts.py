from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

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
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger = logging.getLogger(__name__)
        if status in {405, 422, 500}:
            logger.warning(
                "Prometheus alerts endpoint returned HTTP %s for %s", status, url
            )
        else:
            logger.warning("HTTP %s when fetching alerts from %s", status, url)
        return []
    except Exception as e:  # pragma: no cover - network errors
        logging.getLogger(__name__).warning(
            "Failed to fetch alerts from %s", url, exc_info=e
        )
        return []
    alerts = data.get("data", {}).get("alerts") if isinstance(data, dict) else None
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


async def resolve_alert(alert_id: str) -> bool:
    """Mark an alert resolved via Prometheus if configured."""

    base_url = os.getenv("PROMETHEUS_URL")
    if not base_url:
        return True
    url = base_url.rstrip("/") + f"/api/v1/alerts/{alert_id}/resolve"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url)
            resp.raise_for_status()
    except Exception as e:  # pragma: no cover - network errors
        logging.getLogger(__name__).warning(
            "Failed to resolve alert %s via %s", alert_id, url, exc_info=e
        )
        return False
    return True


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert_endpoint(alert_id: str) -> dict[str, str]:
    """Mark an alert resolved."""

    ok = await resolve_alert(alert_id)
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to resolve alert")
    return {"status": "resolved"}
