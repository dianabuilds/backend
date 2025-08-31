#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _env(key: str, default: str = "") -> str:
    return os.getenv(key) or default


# Добавляем корневую директорию проекта в PYTHONPATH
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))


async def _main():
    # Позволяет разово выполнить одну итерацию при AI_WORKER_ONESHOT=1
    poll = float(_env("AI_WORKER_POLL_INTERVAL", "2.0"))
    # Ленивая загрузка, чтобы импорт не падал без зависимостей
    from apps.backend.app.domains.ai.worker import run_worker_loop

    await run_worker_loop(poll_interval=poll)


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        sys.exit(130)
