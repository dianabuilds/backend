from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    aioredis = None

from apps.backend import get_container
from domains.platform.iam.security import require_admin
from domains.platform.telemetry.application.metrics_registry import llm_metrics
from domains.platform.telemetry.application.worker_metrics_service import worker_metrics
from packages.core.db import get_async_engine

DEFAULT_AUTO_REFRESH_SECONDS = 30


def _safe_iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - defensive
            return str(value)
    try:
        return str(value)
    except Exception:  # pragma: no cover - defensive
        return None


async def _collect_db_and_queue_metrics(settings: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    collected_at = datetime.now(UTC)
    db_signal: dict[str, Any] = {
        "id": "database:primary",
        "label": "Database",
        "status": "unknown",
        "ok": None,
        "latency_ms": None,
        "hint": None,
        "last_heartbeat": _safe_iso(collected_at),
    }
    queue_signal: dict[str, Any] = {
        "id": "queue:worker",
        "label": "Queue",
        "status": "unknown",
        "ok": None,
        "pending": None,
        "leased": None,
        "failed": None,
        "oldest_pending_seconds": None,
        "last_heartbeat": None,
        "hint": None,
    }

    database_url = getattr(settings, "database_url", None)
    if not database_url:
        db_signal["hint"] = "Database URL is not configured"
        queue_signal["hint"] = "Queue metrics unavailable without database"
        return db_signal, queue_signal

    engine = get_async_engine("admin-system", url=database_url)

    start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000.0
        db_signal.update(
            {
                "status": "healthy",
                "ok": True,
                "latency_ms": round(latency_ms, 2),
                "last_heartbeat": _safe_iso(datetime.now(UTC)),
            }
        )
    except Exception as exc:  # pragma: no cover - runtime safeguard
        db_signal.update(
            {
                "status": "critical",
                "ok": False,
                "hint": f"Database ping failed: {exc}",
                "error": str(exc),
                "last_heartbeat": _safe_iso(datetime.now(UTC)),
            }
        )

    try:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text("SELECT status, COUNT(*) AS count FROM worker_jobs GROUP BY status")
                )
            ).mappings()
            counts = {str(row["status"]).lower(): int(row["count"]) for row in rows}

        pending = counts.get("queued", 0)
        failed = counts.get("failed", 0)
        leased = counts.get("leased", 0)
        status = "healthy"
        if failed > 0:
            status = "warning"
        if pending > 1000 or failed > 10:
            status = "critical"

        oldest_seconds = None
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT EXTRACT(EPOCH FROM (now() - MIN(created_at))) AS age "
                    "FROM worker_jobs WHERE status = 'queued'"
                )
            )
            oldest_seconds = result.scalar_one_or_none()

        heartbeat = None
        async with engine.connect() as conn:
            hb = await conn.execute(
                text("SELECT MAX(ts) FROM worker_job_events WHERE event = 'heartbeat'")
            )
            heartbeat = hb.scalar_one_or_none()

        queue_signal.update(
            {
                "status": status,
                "ok": status == "healthy",
                "pending": pending,
                "leased": leased,
                "failed": failed,
                "succeeded": counts.get("completed", counts.get("succeeded", 0)),
                "oldest_pending_seconds": (
                    float(oldest_seconds) if oldest_seconds is not None else None
                ),
                "last_heartbeat": _safe_iso(heartbeat),
            }
        )
    except Exception as exc:  # pragma: no cover - runtime safeguard
        queue_signal.update(
            {
                "status": "unknown",
                "ok": None,
                "hint": f"Queue metrics unavailable: {exc}",
            }
        )

    return db_signal, queue_signal


async def _collect_redis_signal(settings: Any) -> dict[str, Any]:
    signal: dict[str, Any] = {
        "id": "redis:cache",
        "label": "Redis",
        "status": "unknown",
        "ok": None,
        "latency_ms": None,
        "last_heartbeat": None,
        "hint": None,
    }
    redis_url = getattr(settings, "redis_url", None)
    if not redis_url:
        signal["hint"] = "Redis URL is not configured"
        return signal
    if aioredis is None:
        signal.update(
            {
                "status": "unknown",
                "hint": "redis package unavailable, unable to ping cache",
            }
        )
        return signal
    client = aioredis.from_url(str(redis_url))
    start = time.perf_counter()
    try:
        await client.ping()
        latency_ms = (time.perf_counter() - start) * 1000.0
        now = datetime.now(UTC)
        signal.update(
            {
                "status": "healthy",
                "ok": True,
                "latency_ms": round(latency_ms, 2),
                "last_heartbeat": _safe_iso(now),
            }
        )
    except Exception as exc:
        signal.update(
            {
                "status": "critical",
                "ok": False,
                "hint": f"Redis ping failed: {exc}",
            }
        )
    finally:
        try:
            await client.close()
        except Exception:  # pragma: no cover - defensive
            pass
    return signal


def _collect_worker_signals(collected_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    snapshot = worker_metrics.snapshot()
    jobs = snapshot.get("jobs", {}) or {}
    completed = int(jobs.get("completed", jobs.get("succeeded", 0)))
    failed = int(jobs.get("failed", 0))
    total = completed + failed
    failure_rate = (failed / total) if total else 0.0
    status = "healthy"
    if failure_rate >= 0.2:
        status = "critical"
    elif failure_rate >= 0.05:
        status = "warning"

    signal = {
        "id": "worker:aggregate",
        "label": "Workers",
        "status": status,
        "ok": failure_rate < 0.05,
        "avg_duration_ms": float(snapshot.get("job_avg_ms") or 0.0),
        "failure_rate": failure_rate,
        "jobs_completed": completed,
        "jobs_failed": failed,
        "last_heartbeat": collected_at,
        "hint": "Async workers delivering jobs.",
    }
    summary = {
        "worker_avg_ms": float(snapshot.get("job_avg_ms") or 0.0),
        "worker_failure_rate": failure_rate,
    }
    return [signal], summary


def _collect_llm_signals(collected_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    snapshot = llm_metrics.snapshot()
    calls = snapshot.get("calls", []) or []
    success = sum(int(item.get("count", 0)) for item in calls if str(item.get("type")) == "calls")
    errors = sum(int(item.get("count", 0)) for item in calls if str(item.get("type")) == "errors")
    total = success + errors
    success_rate = (success / total) if total else 1.0
    status = "healthy"
    if success_rate < 0.8:
        status = "critical"
    elif success_rate < 0.95:
        status = "warning"

    latency_entries = snapshot.get("latency_avg_ms", []) or []
    avg_latency = 0.0
    if latency_entries:
        avg_latency = sum(float(item.get("avg_ms", 0.0)) for item in latency_entries) / len(
            latency_entries
        )

    signal = {
        "id": "llm:providers",
        "label": "LLM providers",
        "status": status,
        "ok": success_rate >= 0.95,
        "success_rate": success_rate,
        "latency_ms": round(avg_latency, 2) if avg_latency else None,
        "total_calls": total,
        "error_count": errors,
        "last_heartbeat": collected_at,
        "hint": "Model registry and providers.",
    }
    summary = {"llm_success_rate": success_rate}
    return [signal], summary


def _derive_summary(
    collected_at: str,
    db_signal: dict[str, Any],
    queue_signal: dict[str, Any],
    worker_summary: dict[str, Any],
    llm_summary: dict[str, Any],
    incidents: dict[str, Any],
) -> dict[str, Any]:
    return {
        "collected_at": collected_at,
        "db_latency_ms": db_signal.get("latency_ms"),
        "queue_pending": queue_signal.get("pending"),
        "queue_status": queue_signal.get("status"),
        "worker_avg_ms": worker_summary.get("worker_avg_ms"),
        "worker_failure_rate": worker_summary.get("worker_failure_rate"),
        "llm_success_rate": llm_summary.get("llm_success_rate"),
        "active_incidents": len(incidents.get("active", [])),
    }


def _build_links(settings: Any) -> dict[str, str]:
    links: dict[str, str] = {
        "health": "/v1/admin/health",
        "ready": "/v1/admin/readyz",
    }
    docs_url = getattr(settings, "system_docs_url", None)
    if docs_url:
        links["docs"] = str(docs_url)
    runbooks = getattr(settings, "system_runbooks_url", None)
    if runbooks:
        links["runbooks"] = str(runbooks)
    links["alerts_channel"] = "https://slack.com/app_redirect?channel=platform-admin"
    return links


async def _collect_incident_data(settings: Any) -> dict[str, Any]:
    integrations = []
    for item in _integration_overview(settings)["items"]:
        integrations.append(
            {
                "id": item.get("id"),
                "label": item.get("label", item.get("id")),
                "status": item.get("status"),
                "hint": item.get("hint"),
            }
        )
    return {
        "active": [],
        "recent": [],
        "integrations": integrations,
    }


async def _system_overview(settings: Any) -> dict[str, Any]:
    collected_at = datetime.now(UTC).isoformat()
    db_signal, queue_signal = await _collect_db_and_queue_metrics(settings)
    redis_signal = await _collect_redis_signal(settings)
    worker_signals, worker_summary = _collect_worker_signals(collected_at)
    llm_signals, llm_summary = _collect_llm_signals(collected_at)
    incidents = await _collect_incident_data(settings)

    signals = {
        "core": [redis_signal],
        "databases": [db_signal],
        "queues": [queue_signal],
        "workers": worker_signals,
        "llm": llm_signals,
    }

    summary = _derive_summary(
        collected_at, db_signal, queue_signal, worker_summary, llm_summary, incidents
    )

    return {
        "collected_at": collected_at,
        "recommendations": {"auto_refresh_seconds": DEFAULT_AUTO_REFRESH_SECONDS},
        "signals": signals,
        "summary": summary,
        "incidents": incidents,
        "links": _build_links(settings),
        "changelog": [],
    }


def _integration_overview(settings: Any) -> dict[str, Any]:
    topics_raw = (
        getattr(settings, "notify_topics", None) or getattr(settings, "event_topics", "") or ""
    )
    topics = [t.strip() for t in str(topics_raw).split(",") if t.strip()]
    slack_configured = bool(getattr(settings, "notify_webhook_url", None))
    smtp_mock = bool(getattr(settings, "smtp_mock", True))
    smtp_host = getattr(settings, "smtp_host", None)
    smtp_port = getattr(settings, "smtp_port", None)
    smtp_tls = getattr(settings, "smtp_tls", True)
    mail_from = getattr(settings, "smtp_mail_from", None)
    mail_from_name = getattr(settings, "smtp_mail_from_name", None)

    if smtp_mock:
        email_status = "sandbox"
        email_hint = "Mock mode enabled - emails are logged only."
    elif smtp_host:
        email_status = "connected"
        email_hint = "SMTP is configured. Monitor send failures and rate limits."
    else:
        email_status = "disconnected"
        email_hint = "SMTP host is not configured. Notifications will not be delivered."

    return {
        "collected_at": datetime.now(UTC).isoformat(),
        "items": [
            {
                "id": "slack",
                "label": "Slack",
                "status": "connected" if slack_configured else "disconnected",
                "connected": slack_configured,
                "topics": topics,
                "hint": (
                    "Incoming webhook active. Alerts are mirrored to Slack."
                    if slack_configured
                    else "Set APP_NOTIFY_WEBHOOK_URL to forward alerts into Slack."
                ),
            },
            {
                "id": "webhook",
                "label": "Webhook",
                "status": "ready" if topics else "pending",
                "topics": topics,
                "event_group": getattr(settings, "event_group", None),
                "idempotency_ttl": getattr(settings, "event_idempotency_ttl", None),
                "hint": (
                    "Registered webhooks receive JSON payloads from /v1/notifications/send."
                    if topics
                    else "Configure APP_NOTIFY_TOPICS or APP_EVENT_TOPICS to start publishing events."
                ),
            },
            {
                "id": "email",
                "label": "Email",
                "status": email_status,
                "connected": (not smtp_mock) and bool(smtp_host),
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "smtp_tls": smtp_tls,
                "smtp_mock": smtp_mock,
                "mail_from": mail_from,
                "mail_from_name": mail_from_name,
                "hint": email_hint,
            },
        ],
    }


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])

    @router.get("/health")
    async def health() -> dict[str, Any]:
        return {"ok": True}

    @router.get("/readyz")
    async def readyz() -> dict[str, Any]:
        return {"ok": True}

    @router.get("/config")
    async def config(req: Request) -> dict[str, Any]:
        container = get_container(req)
        settings = container.settings
        return {
            "env": settings.env,
            "database_url": str(settings.database_url) if settings.database_url else None,
            "redis_url": str(settings.redis_url) if settings.redis_url else None,
            "event_topics": settings.event_topics,
            "event_group": settings.event_group,
        }

    @router.get("/integrations")
    async def integrations(req: Request) -> dict[str, Any]:
        container = get_container(req)
        return _integration_overview(container.settings)

    @router.get("/system/overview")
    async def system_overview(req: Request) -> dict[str, Any]:
        container = get_container(req)
        return await _system_overview(container.settings)

    return router
