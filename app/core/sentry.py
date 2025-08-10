from __future__ import annotations

from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import Settings


SENSITIVE_KEYS = {"password", "token", "authorization"}


def _before_send(event: dict[str, Any], hint: Any) -> dict[str, Any] | None:
    request = event.get("request", {})
    data = request.get("data")
    if isinstance(data, dict):
        for key in list(data.keys()):
            if key.lower() in SENSITIVE_KEYS:
                data[key] = "[Filtered]"
    headers = request.get("headers")
    if isinstance(headers, dict):
        for key in list(headers.keys()):
            if key.lower() in SENSITIVE_KEYS:
                headers[key] = "[Filtered]"
    return event


def init_sentry(settings: Settings) -> None:
    if not settings.sentry.dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry.dsn,
        integrations=[FastApiIntegration(), StarletteIntegration()],
        traces_sample_rate=settings.sentry.traces_sample_rate,
        environment=settings.sentry.env or settings.environment,
        before_send=_before_send,
    )
