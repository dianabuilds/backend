from __future__ import annotations

import os
from functools import lru_cache

from apps.backend.app.api_gateway.wires import Container, build_container


@lru_cache(maxsize=1)
def get_worker_container() -> Container:
    """Build and cache the application container for background workers."""
    env = os.getenv("APP_ENV")
    if env:
        return build_container(env=env)
    return build_container()


__all__ = ["get_worker_container"]
