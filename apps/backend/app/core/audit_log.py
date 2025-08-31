"""Helpers for logging admin actions.

This module was previously incomplete which resulted in import errors during
application start-up.  The admin routers depend on :func:`log_admin_action`,
therefore the missing imports caused those routers to be skipped and the
frontend received 404 responses when requesting admin data.  Restoring the
required imports ensures the module loads correctly and admin endpoints are
registered.
"""

import asyncio
import logging
from typing import Any

from app.core.db.session import db_session, get_current_session
from app.core.log_filters import ip_var, ua_var
from app.domains.admin.infrastructure.models.audit_log import AuditLog


class AuditLogHandler(logging.Handler):
    """Logging handler that persists admin actions to the database."""

    def emit(
        self, record: logging.LogRecord
    ) -> None:  # pragma: no cover - side effects
        try:
            if record.msg != "admin_action":
                return
            data: dict[str, Any] = {
                "actor_id": getattr(record, "actor_id", None),
                "action": getattr(record, "action", None),
                "resource_type": getattr(record, "resource_type", None),
                "resource_id": getattr(record, "resource_id", None),
                "workspace_id": getattr(record, "workspace_id", None),
                "before": getattr(record, "before", None),
                "after": getattr(record, "after", None),
                "ip": ip_var.get(),
                "user_agent": ua_var.get(),
            }
            # capture any additional extras
            extras = {}
            for key, value in record.__dict__.items():
                if key in {
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "actor_id",
                    "action",
                    "resource_type",
                    "resource_id",
                    "before",
                    "after",
                }:
                    continue
                extras[key] = value
            if extras:
                data["extra"] = extras
            session = get_current_session()
            if session is not None:
                session.add(AuditLog(**data))
            else:
                asyncio.create_task(self._save(data))
        except Exception:  # pragma: no cover - avoid logging recursion
            pass

    async def _save(self, data: dict[str, Any]) -> None:
        async with db_session() as session:
            session.add(AuditLog(**data))


async def log_admin_action(
    session,
    *,
    actor_id=None,
    action: str,
    resource_type=None,
    resource_id=None,
    before=None,
    after=None,
    workspace_id=None,
    **extra,
) -> None:
    log = AuditLog(
        actor_id=str(actor_id) if actor_id else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        workspace_id=workspace_id,
        before=before,
        after=after,
        ip=ip_var.get(),
        user_agent=ua_var.get(),
        extra=extra or None,
    )
    session.add(log)
