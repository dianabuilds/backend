from __future__ import annotations

import importlib
import sys

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.admin.infrastructure.models.audit_log import AuditLog  # noqa: E402


def test_audit_log_has_workspace_id_column() -> None:
    columns = {c.name for c in AuditLog.__table__.columns}
    assert "workspace_id" in columns
