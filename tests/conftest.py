from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import Generator
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _PROJECT_ROOT / "apps/backend"
for candidate in (_PROJECT_ROOT, _BACKEND_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)
pytest_plugins = [
    "domains.platform.moderation.tests.fixtures",
]


_BACKEND_PATH = _BACKEND_ROOT


def _ensure_backend_on_path() -> str:
    backend_str = str(_BACKEND_PATH)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)
    return backend_str


@pytest.fixture(scope="session", autouse=True)
def _add_backend_to_sys_path() -> Generator[None, None, None]:
    backend_str = _ensure_backend_on_path()
    yield
    if backend_str in sys.path:
        sys.path.remove(backend_str)


@pytest.fixture(autouse=True)
def _ensure_event_loop() -> Generator[None, None, None]:
    asyncio.set_event_loop(asyncio.new_event_loop())
    yield


def make_jwt(sub: str, role: str = "user") -> str:
    _ensure_backend_on_path()
    from packages.core.config import load_settings

    settings = load_settings()
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + 600}
    return jwt.encode(
        payload, key=settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm
    )


def add_auth(client: TestClient, token: str) -> None:
    _ensure_backend_on_path()
    from packages.core.config import load_settings

    settings = load_settings()
    client.cookies.set("access_token", token)
    client.cookies.set(settings.auth_csrf_cookie_name, "csrf-test")


@pytest.fixture(scope="session")
def app_client() -> Generator[TestClient, None, None]:
    _ensure_backend_on_path()
    from apps.backend.app.api_gateway.main import app as fastapi_app

    with TestClient(fastapi_app) as client:
        yield client
