from __future__ import annotations

from dataclasses import dataclass

from domains.platform.audit.adapters.memory.repository import InMemoryAuditRepo
from domains.platform.audit.adapters.sql.repository import SQLAuditRepo
from domains.platform.audit.application.service import AuditService
from domains.platform.audit.ports.repo import AuditLogRepository
from packages.core.config import Settings, load_settings, to_async_dsn
from packages.core.testing import is_test_mode


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


def build_container(settings: Settings | None = None) -> AuditContainer:
    cfg = settings or load_settings()
    if is_test_mode(cfg):
        repo: AuditLogRepository = InMemoryAuditRepo()
        return AuditContainer(repo=repo, service=AuditService(repo))

    if not getattr(cfg, "database_url", None):
        raise RuntimeError("APP_DATABASE_URL is required for audit repository")
    if not _db_reachable(str(cfg.database_url)):
        raise RuntimeError("database is unreachable for audit repository")
    dsn = to_async_dsn(cfg.database_url)
    if isinstance(dsn, str) and "?" in dsn:
        dsn = dsn.split("?", 1)[0]
    repo = SQLAuditRepo(dsn)
    svc = AuditService(repo)
    return AuditContainer(repo=repo, service=svc)


__all__ = ["AuditContainer", "build_container"]
