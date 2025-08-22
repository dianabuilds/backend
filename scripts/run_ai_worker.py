#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys


def _env(key: str, default: str = "") -> str:
    return os.getenv(key) or default


async def _main():
    # Позволяет разово выполнить одну итерацию при AI_WORKER_ONESHOT=1
    poll = float(_env("AI_WORKER_POLL_INTERVAL", "2.0"))
    # Ленивая загрузка, чтобы импорт не падал без зависимостей
    from app.engine.ai_worker import run_worker_loop
    await run_worker_loop(poll_interval=poll)


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        sys.exit(130)
