from __future__ import annotations

import logging
from contextvars import ContextVar

# Request-scoped logging context variables
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
ip_var: ContextVar[str | None] = ContextVar("ip", default=None)
ua_var: ContextVar[str | None] = ContextVar("ua", default=None)
profile_id_var: ContextVar[str | None] = ContextVar("profile_id", default=None)


class RequestContextFilter(logging.Filter):
    def __init__(self, service: str = "backend") -> None:
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        record.service = self.service
        record.request_id = request_id_var.get() or "-"
        record.user_id = user_id_var.get() or "-"
        record.ip = ip_var.get() or "-"
        record.user_agent = ua_var.get() or "-"
        record.profile_id = profile_id_var.get() or "-"
        return True


__all__ = [
    "request_id_var",
    "user_id_var",
    "ip_var",
    "ua_var",
    "profile_id_var",
    "RequestContextFilter",
]

