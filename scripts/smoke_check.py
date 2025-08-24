#!/usr/bin/env python3
"""Minimal smoke test for a running backend instance."""
import asyncio
import sys

import httpx


async def check(base_url: str) -> int:
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(f"{base_url}/health")
        if r.status_code != 200 or r.json().get("status") != "ok":
            print("Health check failed", r.text)
            return 1
        r = await client.get(f"{base_url}/openapi.json")
        if r.status_code != 200 or "workspace_id" not in r.text:
            print("OpenAPI check failed")
            return 1
    print("Smoke check passed")
    return 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run basic health and OpenAPI checks")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    code = asyncio.run(check(args.base_url))
    sys.exit(code)


if __name__ == "__main__":
    main()
