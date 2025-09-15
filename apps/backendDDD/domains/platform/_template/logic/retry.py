from __future__ import annotations

from functools import wraps
from time import sleep


def with_retry(attempts: int = 3, backoff: float = 0.1):
    def deco(fn):
        @wraps(fn)
        def inner(*a, **kw):
            last = None
            for i in range(attempts):
                try:
                    return fn(*a, **kw)
                except Exception as e:  # pragma: no cover - template
                    last = e
                    sleep(backoff * (2**i))
            if last:
                raise last

        return inner

    return deco
