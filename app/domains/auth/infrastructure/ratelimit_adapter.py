from __future__ import annotations

from typing import Callable, Any

from app.domains.auth.application.ports.ratelimit_port import IRateLimiter
from app.core.rate_limit import rate_limit_dep, rate_limit_dep_key


class CoreRateLimiter(IRateLimiter):
    def dependency(self, key: str | None = None) -> Callable[..., Any]:
        return rate_limit_dep_key(key) if key else rate_limit_dep
