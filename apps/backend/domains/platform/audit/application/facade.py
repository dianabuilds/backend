from __future__ import annotations

from domains.platform.audit.infrastructure import (
    AuditLogPayload as _AuditLogPayload,
)
from domains.platform.audit.infrastructure import (
    safe_audit_log as _safe_audit_log,
)

AuditLogPayload = _AuditLogPayload
safe_audit_log = _safe_audit_log

__all__ = ["AuditLogPayload", "safe_audit_log"]
