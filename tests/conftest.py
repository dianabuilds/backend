from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _add_backend_to_sys_path() -> None:
    backend_path = Path(__file__).resolve().parents[1] / "app/backend"
    sys.path.insert(0, str(backend_path))
    yield
    sys.path.remove(str(backend_path))


@pytest.fixture(autouse=True)
def _ensure_event_loop() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    yield
