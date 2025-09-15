from __future__ import annotations

from functools import wraps
from time import time
from typing import Callable, Dict

_buckets: Dict[str, list[float]] = {}


def rate_limited(key: str, qps: int):  # pragma: no cover - template
    window = 1.0

    def deco(fn: Callable[..., object]):
        @wraps(fn)
        def inner(*a: object, **kw: object) -> object:
            now = time()
            bucket = _buckets.setdefault(key, [])
            # drop old
            while bucket and now - bucket[0] > window:
                bucket.pop(0)
            if len(bucket) >= qps:
                raise RuntimeError("Rate limit exceeded")
            bucket.append(now)
            return fn(*a, **kw)

        return inner

    return deco
