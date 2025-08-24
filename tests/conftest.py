import asyncio
import pytest

@pytest.fixture(autouse=True)
def _ensure_event_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())
    yield
