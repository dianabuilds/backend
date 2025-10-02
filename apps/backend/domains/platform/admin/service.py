from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from packages.core.config import Settings

from .adapters.database import DatabaseProbe
from .adapters.metrics import MetricsProbe
from .adapters.redis import RedisProbe

DEFAULT_AUTO_REFRESH_SECONDS = 30


def _safe_iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        iso_fn = value.isoformat  # type: ignore[attr-defined]
        try:
            return iso_fn()  # type: ignore[misc]
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return str(value)
    return str(value)


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


@dataclass
class AdminService:
    settings: Settings
    database_probe: DatabaseProbe
    redis_probe: RedisProbe
    metrics_probe: MetricsProbe

    def get_config(self) -> dict[str, object | None]:
        settings = self.settings
        return {
            "env": settings.env,
            "database_url": (
                str(settings.database_url) if settings.database_url else None
            ),
            "redis_url": str(settings.redis_url) if settings.redis_url else None,
            "event_topics": settings.event_topics,
            "event_group": settings.event_group,
        }

    def get_integrations(self) -> dict[str, Any]:
        settings = self.settings
        topics_raw = (
            getattr(settings, "notify_topics", None)
            or getattr(settings, "event_topics", "")
            or ""
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
            email_hint = (
                "SMTP host is not configured. Notifications will not be delivered."
            )

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

    async def get_system_overview(self) -> dict[str, Any]:
        collected_at = datetime.now(UTC)
        db_signal, queue_signal = await self._collect_db_and_queue()
        redis_signal = await self.redis_probe.ping()
        worker_signals, worker_summary = self.metrics_probe.worker_signals(
            _safe_iso(collected_at) or ""
        )
        llm_signals, llm_summary = self.metrics_probe.llm_signals(
            _safe_iso(collected_at) or ""
        )
        incidents = await self._collect_incident_data()

        signals = {
            "core": [redis_signal],
            "databases": [db_signal],
            "queues": [queue_signal],
            "workers": worker_signals,
            "llm": llm_signals,
        }

        summary = self._derive_summary(
            collected_at,
            db_signal,
            queue_signal,
            worker_summary,
            llm_summary,
            incidents,
        )

        return {
            "collected_at": collected_at,
            "recommendations": {"auto_refresh_seconds": DEFAULT_AUTO_REFRESH_SECONDS},
            "signals": signals,
            "summary": summary,
            "incidents": incidents,
            "links": self._build_links(),
            "changelog": [],
        }

    async def _collect_db_and_queue(self) -> tuple[dict[str, Any], dict[str, Any]]:
        db_signal: dict[str, Any] = {
            "id": "database:primary",
            "label": "Database",
            "status": "unknown",
            "ok": None,
            "latency_ms": None,
            "hint": None,
            "last_heartbeat": None,
            "error": None,
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
            "error": None,
        }

        database_url = getattr(self.settings, "database_url", None)
        if not database_url:
            db_signal["hint"] = "Database URL is not configured"
            queue_signal["hint"] = "Queue metrics unavailable without database"
            return db_signal, queue_signal

        latency_ms, error = await self.database_probe.ping()
        db_signal.update(
            {
                "status": "healthy" if latency_ms is not None else "critical",
                "ok": latency_ms is not None,
                "latency_ms": latency_ms,
                "error": error,
                "last_heartbeat": datetime.now(UTC),
            }
        )
        stats = await self.database_probe.queue_stats()
        queue_signal.update(stats)
        queue_signal["last_heartbeat"] = _safe_iso(queue_signal.get("last_heartbeat"))
        queue_signal["oldest_pending_seconds"] = _as_float(
            queue_signal.get("oldest_pending_seconds")
        )
        return db_signal, queue_signal

    async def _collect_incident_data(self) -> dict[str, Any]:
        overview = self.get_integrations()
        integrations = [
            {
                "id": item.get("id"),
                "label": item.get("label", item.get("id")),
                "status": item.get("status"),
                "hint": item.get("hint"),
            }
            for item in overview.get("items", [])
        ]
        return {
            "active": [],
            "recent": [],
            "integrations": integrations,
        }

    def _derive_summary(
        self,
        collected_at: datetime,
        db_signal: dict[str, Any],
        queue_signal: dict[str, Any],
        worker_summary: dict[str, Any],
        llm_summary: dict[str, Any],
        incidents: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "collected_at": _safe_iso(collected_at),
            "db_latency_ms": db_signal.get("latency_ms"),
            "queue_pending": queue_signal.get("pending"),
            "queue_status": queue_signal.get("status"),
            "worker_avg_ms": worker_summary.get("worker_avg_ms"),
            "worker_failure_rate": worker_summary.get("worker_failure_rate"),
            "llm_success_rate": llm_summary.get("llm_success_rate"),
            "active_incidents": len(incidents.get("active", [])),
        }

    def _build_links(self) -> dict[str, str]:
        links: dict[str, str] = {
            "health": "/v1/admin/health",
            "ready": "/v1/admin/readyz",
        }
        settings = self.settings
        docs_url = getattr(settings, "system_docs_url", None)
        if docs_url:
            links["docs"] = str(docs_url)
        runbooks = getattr(settings, "system_runbooks_url", None)
        if runbooks:
            links["runbooks"] = str(runbooks)
        links["alerts_channel"] = (
            "https://slack.com/app_redirect?channel=platform-admin"
        )
        return links


__all__ = ["AdminService"]
