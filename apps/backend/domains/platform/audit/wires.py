from __future__ import annotations

from dataclasses import dataclass

from domains.platform.audit.adapters.repo_memory import (
    InMemoryAuditRepo,
)
from domains.platform.audit.adapters.repo_sql import SQLAuditRepo
from domains.platform.audit.application.service import AuditService
from domains.platform.audit.ports.repo import AuditLogRepository


@dataclass
class AuditContainer:
    repo: AuditLogRepository
    service: AuditService


def _db_reachable(url: str) -> bool:
    try:
        import socket
        from urllib.parse import urlparse

        u = urlparse(url)
        host = u.hostname or "localhost"
        port = u.port or 5432
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except Exception:
        return False


def build_container() -> AuditContainer:
    repo: AuditLogRepository = InMemoryAuditRepo()
    # Try SQL if DB configured and reachable
    try:
        from packages.core.config import load_settings, to_async_dsn  # type: ignore

        s = load_settings()
        if s.database_url and _db_reachable(str(s.database_url)):
            dsn = to_async_dsn(s.database_url)
            # Some providers append libpq/psycopg-only params; trim for asyncpg
            if isinstance(dsn, str) and "?" in dsn:
                dsn = dsn.split("?", 1)[0]
            if dsn:
                repo = SQLAuditRepo(dsn)  # type: ignore[assignment]
    except Exception:
        pass
    svc = AuditService(repo)
    return AuditContainer(repo=repo, service=svc)


__all__ = ["AuditContainer", "build_container"]
