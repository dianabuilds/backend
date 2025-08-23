from __future__ import annotations

from typing import Any, Callable

from fastapi.params import Depends as _Depends

from app.domains.auth.application.ports.ratelimit_port import IRateLimiter
from app.core.rate_limit import rate_limit_dep, rate_limit_dep_key


class CoreRateLimiter(IRateLimiter):
    def dependency(self, key: str | None = None) -> Callable[..., Any]:
        dep = rate_limit_dep_key(key) if key else rate_limit_dep
        if isinstance(dep, _Depends):
            return dep.dependency  # unwrap Depends
        return dep
