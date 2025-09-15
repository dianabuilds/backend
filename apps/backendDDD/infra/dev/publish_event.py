from __future__ import annotations

import argparse
import json
from typing import Any

from apps.backendDDD.packages.core.config import load_settings
from apps.backendDDD.packages.core.redis_outbox import RedisOutboxCore


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a dev event to Redis Streams")
    parser.add_argument("--topic", required=True, help="Topic, e.g. profile.updated.v1")
    parser.add_argument(
        "--payload",
        required=True,
        help='JSON payload string, e.g. {"id":"u1","username":"neo"}',
    )
    parser.add_argument("--key", default=None, help="Optional dedup/partition key")
    parser.add_argument(
        "--redis-url",
        default=None,
        help="Override Redis URL (defaults to APP_REDIS_URL from settings)",
    )
    args = parser.parse_args()
    s = load_settings()
    redis_url = str(args.redis_url or s.redis_url)
    payload: dict[str, Any] = json.loads(args.payload)
    outbox = RedisOutboxCore(redis_url)
    msg_id = outbox.publish(args.topic, payload, key=args.key)
    print(f"published: topic={args.topic} id={msg_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
