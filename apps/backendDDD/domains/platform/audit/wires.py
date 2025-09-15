from __future__ import annotations

from dataclasses import dataclass

from apps.backendDDD.domains.platform.audit.adapters.repo_memory import (
    InMemoryAuditRepo,
)
from apps.backendDDD.domains.platform.audit.application.service import AuditService


@dataclass
class AuditContainer:
    repo: InMemoryAuditRepo
    service: AuditService


def build_container() -> AuditContainer:
    repo = InMemoryAuditRepo()
    svc = AuditService(repo)
    return AuditContainer(repo=repo, service=svc)


__all__ = ["AuditContainer", "build_container"]
