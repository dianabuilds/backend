import logging
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
ip_var: ContextVar[str | None] = ContextVar("ip", default=None)
ua_var: ContextVar[str | None] = ContextVar("ua", default=None)
workspace_id_var: ContextVar[str | None] = ContextVar("workspace_id", default=None)
account_id_var: ContextVar[str | None] = ContextVar("account_id", default=None)


class RequestContextFilter(logging.Filter):
    def __init__(self, service: str = "backend") -> None:
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        record.request_id = request_id_var.get() or "-"
        record.user_id = user_id_var.get() or "-"
        record.ip = ip_var.get() or "-"
        record.user_agent = ua_var.get() or "-"
        record.workspace_id = workspace_id_var.get() or "-"
        record.account_id = account_id_var.get() or "-"
        return True
