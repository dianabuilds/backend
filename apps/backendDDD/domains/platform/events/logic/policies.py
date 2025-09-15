from __future__ import annotations

import redis  # type: ignore


def rate_limit(r: redis.Redis, key: str, limit: int, window_sec: int = 1) -> bool:
    # INCR and expire
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_sec)
    count, _ = pipe.execute()
    return int(count) <= limit
