from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from domains.platform.audit.application.service import AuditService


@dataclass(slots=True)
class AuditLogPayload:
    """Value object describing a single audit log entry."""

    actor_id: str | None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    before: Any = None
    after: Any = None
    ip: str | None = None
    user_agent: str | None = None
    reason: str | None = None
    extra: Any = None

    def as_kwargs(self) -> dict[str, Any]:
        return asdict(self)


async def safe_audit_log(
    service: AuditService | None,
    payload: AuditLogPayload,
    *,
    logger: logging.Logger,
    error_slug: str,
    suppressed: Iterable[type[Exception]] | None = None,
    log_extra: dict[str, Any] | None = None,
) -> None:
    """Log audit entry via service, swallowing expected errors."""

    if service is None:
        return
    suppressed_types = tuple(suppressed or (Exception,))
    try:
        await service.log(**payload.as_kwargs())
    except suppressed_types as exc:  # type: ignore[misc]
        logger.warning(error_slug, extra=log_extra, exc_info=exc)


__all__ = ["AuditLogPayload", "safe_audit_log"]
