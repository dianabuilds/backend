from __future__ import annotations

import os
from typing import Any

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
    # Разрешаем отключать через .env SENTRY_ENABLED=false; по умолчанию включено
    env_flag = os.getenv("SENTRY_ENABLED")
    if env_flag is not None:
        enabled = env_flag.strip().lower() in {"1", "true", "yes", "on"}
    else:
        enabled = getattr(getattr(settings, "sentry", object()), "enabled", True)

    if not enabled:
        return

    dsn = getattr(getattr(settings, "sentry", object()), "dsn", None)
    if not dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        # Пакет не установлен — игнорируем инициализацию
        return

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FastApiIntegration(), StarletteIntegration()],
        traces_sample_rate=getattr(getattr(settings, "sentry", object()), "traces_sample_rate", 0.0),
        environment=(getattr(getattr(settings, "sentry", object()), "env", None) or getattr(settings, "environment", None)),
        before_send=_before_send,
    )
