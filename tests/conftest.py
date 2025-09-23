from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_backend_path = Path(__file__).resolve().parents[1] / "apps/backend"
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

import pytest


@pytest.fixture(scope="session", autouse=True)
def _add_backend_to_sys_path() -> None:
    backend_path = Path(__file__).resolve().parents[1] / "apps/backend"
    sys.path.insert(0, str(backend_path))
    yield
    sys.path.remove(str(backend_path))


@pytest.fixture(autouse=True)
def _ensure_event_loop() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    yield


import time

import jwt

from packages.core.config import load_settings


def make_jwt(sub: str, role: str = "user") -> str:
    settings = load_settings()
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + 600}
    return jwt.encode(payload, key=settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)


def add_auth(client, token: str) -> None:
    settings = load_settings()
    client.cookies.set("access_token", token)
    client.cookies.set(settings.auth_csrf_cookie_name, "csrf-test")


from fastapi.testclient import TestClient

from app.api_gateway.main import app as fastapi_app


@pytest.fixture(scope="session")
def app_client():
    with TestClient(fastapi_app) as client:
        yield client
