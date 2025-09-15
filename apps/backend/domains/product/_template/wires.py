from __future__ import annotations

from dataclasses import dataclass

from domains.platform.events.adapters.outbox_redis import (
    RedisOutbox as ProductOutboxRedis,
)

from .adapters.iam_client import IamClientImpl as ProductIamClient
from .adapters.repo_sql import SQLRepo as ProductSQLRepo
from .application.ports import Flags

# Note: In real domains import these from your shared packages, e.g.:
# from apps.backendDDD.packages.core.config import load_settings, Settings
# from apps.backendDDD.packages.core.flags import Flags
from .application.services import Service as ProductService


@dataclass(slots=True)
class Container:
    settings: object  # replace with real Settings
    product_service: ProductService


def load_settings() -> object:  # placeholder to keep template self-contained
    class _S:
        database_url = "postgresql://user:pass@localhost:5432/app"
        redis_url = "redis://localhost:6379/0"
        iam_url = "http://localhost:8000"

    return _S()


def build_container(env: str = "dev") -> Container:
    settings = load_settings()
    repo = ProductSQLRepo(str(settings.database_url))
    outbox = ProductOutboxRedis(str(settings.redis_url))
    iam = ProductIamClient(str(settings.iam_url))
    svc = ProductService(repo=repo, outbox=outbox, iam=iam, flags=Flags())
    return Container(settings=settings, product_service=svc)
