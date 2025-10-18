from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from packages.fastapi_rate_limit import LimiterDependencies, optional_rate_limiter


@dataclass(frozen=True)
class RateLimitSpec:
    key: str
    times: int
    seconds: int
    burst: int | None = None
    description: str | None = None

    def as_dependencies(self) -> LimiterDependencies:
        return optional_rate_limiter(times=self.times, seconds=self.seconds)

    def to_payload(self) -> dict[str, int]:
        payload: dict[str, int] = {"times": self.times, "seconds": self.seconds}
        if self.burst is not None:
            payload["burst"] = int(self.burst)
        return payload


PUBLIC_RATE_LIMITS: Mapping[str, RateLimitSpec] = {
    "nodes": RateLimitSpec(
        key="nodes", times=60, seconds=60, description="Public node write operations"
    ),
    "navigation": RateLimitSpec(
        key="navigation",
        times=30,
        seconds=60,
        description="Navigation state transitions",
    ),
    "content": RateLimitSpec(
        key="content", times=20, seconds=60, description="Public content queries"
    ),
}


def public_rate_limits_payload() -> dict[str, dict[str, int]]:
    return {name: spec.to_payload() for name, spec in PUBLIC_RATE_LIMITS.items()}


__all__ = ["RateLimitSpec", "PUBLIC_RATE_LIMITS", "public_rate_limits_payload"]
