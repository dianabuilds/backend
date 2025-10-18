from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.platform.events.application.publisher import OutboxPublisher

from .adapters.iam_client import IamClientImpl as ProductIamClient
from .adapters.sql.repository import SQLRepo as ProductSQLRepo
from .application.ports import Flags

# Note: In real domains import these from your shared packages, e.g.:
# from apps.backend.packages.core.config import load_settings, Settings
# from apps.backend.packages.core.flags import Flags
from .application.services import Service as ProductService


@dataclass(slots=True)
class Container:
    settings: Any  # replace with real Settings
    product_service: ProductService


def load_settings() -> Any:  # placeholder to keep template self-contained
    class _S:
        database_url = "postgresql://user:pass@localhost:5432/app"
        redis_url = "redis://localhost:6379/0"
        iam_url = "http://localhost:8000"

    return _S()


def build_container(env: str = "dev") -> Container:
    settings = load_settings()
    repo = ProductSQLRepo(str(settings.database_url))
    outbox: OutboxPublisher | None = None  # resolve via container_registry in real code
    iam = ProductIamClient(str(settings.iam_url))
    svc = ProductService(repo=repo, outbox=outbox, iam=iam, flags=Flags())
    return Container(settings=settings, product_service=svc)
