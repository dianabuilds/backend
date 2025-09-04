from __future__ import annotations

from app.domains.admin.infrastructure.models.audit_log import AuditLog


def test_audit_log_has_workspace_id_column() -> None:
    columns = {c.name for c in AuditLog.__table__.columns}
    assert "workspace_id" in columns
