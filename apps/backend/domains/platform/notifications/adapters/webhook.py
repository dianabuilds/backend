from __future__ import annotations

import logging

try:  # optional dependency
    import httpx  # type: ignore[import-untyped]
    from httpx import HTTPError as HTTPXError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]
    HTTPXError = Exception  # type: ignore[misc, assignment]


from domains.platform.notifications.logic.dispatcher import (
    register_channel,
)


def register_webhook_channel(url: str, name: str = "webhook") -> None:
    log = logging.getLogger("notifications.webhook")
    if not url:
        return

    def _send(payload: dict) -> None:
        if httpx is None:  # pragma: no cover - optional
            log.warning("httpx not installed; dropping webhook notification")
            return
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(url, json=payload)
        except (HTTPXError, OSError) as exc:  # pragma: no cover - best effort
            log.exception("webhook send failed", exc_info=exc)

    register_channel(name, _send)


__all__ = ["register_webhook_channel"]
