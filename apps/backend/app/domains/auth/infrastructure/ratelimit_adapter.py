from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi.params import Depends as _Depends

from app.kernel.middlewares.rate_limit import rate_limit_dep, rate_limit_dep_key
from app.domains.auth.application.ports.ratelimit_port import IRateLimiter


class CoreRateLimiter(IRateLimiter):
    def dependency(self, key: str | None = None) -> Callable[..., Any]:
        dep = rate_limit_dep_key(key) if key else rate_limit_dep
        if isinstance(dep, _Depends):
            return dep.dependency  # unwrap Depends
        return dep
