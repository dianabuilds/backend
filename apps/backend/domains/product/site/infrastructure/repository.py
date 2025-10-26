from __future__ import annotations

from .repositories.audit import AuditRepositoryMixin
from .repositories.base import EngineFactory, SiteRepositoryBase
from .repositories.global_blocks import GlobalBlockRepositoryMixin
from .repositories.metrics import MetricsRepositoryMixin
from .repositories.pages import PageRepositoryMixin


class SiteRepository(
    SiteRepositoryBase,
    PageRepositoryMixin,
    GlobalBlockRepositoryMixin,
    MetricsRepositoryMixin,
    AuditRepositoryMixin,
):
    def __init__(self, engine_factory: EngineFactory) -> None:
        super().__init__(engine_factory)


__all__ = ["SiteRepository", "EngineFactory"]
