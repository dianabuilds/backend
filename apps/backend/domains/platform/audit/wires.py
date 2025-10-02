from __future__ import annotations

from dataclasses import dataclass

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
    except (OSError, ValueError):
        return False


from packages.core.config import load_settings, to_async_dsn


def build_container() -> AuditContainer:
    settings = load_settings()
    if not settings.database_url:
        raise RuntimeError("APP_DATABASE_URL is required for audit repository")
    if not _db_reachable(str(settings.database_url)):
        raise RuntimeError("database is unreachable for audit repository")
    dsn = to_async_dsn(settings.database_url)
    if isinstance(dsn, str) and "?" in dsn:
        dsn = dsn.split("?", 1)[0]
    repo: AuditLogRepository = SQLAuditRepo(dsn)
    svc = AuditService(repo)
    return AuditContainer(repo=repo, service=svc)


__all__ = ["AuditContainer", "build_container"]
