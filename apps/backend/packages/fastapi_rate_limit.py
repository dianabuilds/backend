from __future__ import annotations

from fastapi import Depends

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    RateLimiter = None  # type: ignore[assignment]

LimiterDependencies = tuple[Depends, ...]


def optional_rate_limiter(*, times: int, seconds: int) -> LimiterDependencies:
    """Return rate-limiter dependency tuple if limiter is available."""

    if RateLimiter is None:
        return ()
    return (Depends(RateLimiter(times=times, seconds=seconds)),)


__all__ = ["LimiterDependencies", "optional_rate_limiter"]
