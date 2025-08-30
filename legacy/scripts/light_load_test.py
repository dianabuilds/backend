# DEPRECATED: legacy script, use dedicated load testing tools
"""Asynchronous lightweight load tester.

Usage:
    python scripts/light_load_test.py --base-url http://localhost:8000 \
        --endpoint /auth/health --endpoint /auth/login --concurrency 5 --duration 10
"""

import argparse
import asyncio
import statistics
import time
from collections import defaultdict

import httpx


async def worker(client: httpx.AsyncClient, url: str, end: float, stats: dict) -> None:
    while time.perf_counter() < end:
        start = time.perf_counter()
        try:
            resp = await client.get(url)
            latency = time.perf_counter() - start
            stats["latencies"].append(latency)
            stats["codes"][resp.status_code] += 1
        except Exception:
            stats["errors"] += 1
        await asyncio.sleep(0)


async def run(
    base_url: str, endpoints: list[str], concurrency: int, duration: int
) -> None:
    end = time.perf_counter() + duration
    stats = {"latencies": [], "codes": defaultdict(int), "errors": 0}
    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        tasks = []
        for _ in range(concurrency):
            for ep in endpoints:
                tasks.append(asyncio.create_task(worker(client, ep, end, stats)))
        await asyncio.gather(*tasks)

    total = len(stats["latencies"])
    mean = statistics.mean(stats["latencies"]) if stats["latencies"] else 0
    p95 = statistics.quantiles(stats["latencies"], n=100)[94] if total else 0
    print("Requests:", total)
    print("Errors:", stats["errors"])
    print("Codes:", dict(stats["codes"]))
    print("Mean latency: {:.3f}s".format(mean))
    print("p95 latency: {:.3f}s".format(p95))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lightweight async load test")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--endpoint", action="append", default=["/health"], help="Endpoint to hit"
    )
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    args = parser.parse_args()
    asyncio.run(run(args.base_url, args.endpoint, args.concurrency, args.duration))
