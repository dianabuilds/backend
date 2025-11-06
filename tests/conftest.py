from __future__ import annotations

import asyncio
import sys
import time
import os
from collections.abc import Generator
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi.testclient import TestClient


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _PROJECT_ROOT / "apps/backend"
for candidate in (_PROJECT_ROOT, _BACKEND_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


def _load_backend_env() -> None:
    env_path = _BACKEND_ROOT / ".env"
    if not env_path.exists():
        return

    wanted_keys = {"APP_DATABASE_URL", "APP_DATABASE_SSL_CA"}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in wanted_keys:
            continue
        value = value.strip().strip('"').strip("'")
        if not value:
            continue
        if key == "APP_DATABASE_SSL_CA" and not Path(value).is_absolute():
            value_path = (_BACKEND_ROOT / value).resolve()
            value = str(value_path)
        os.environ.setdefault(key, value)


def _normalize_database_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return url
    query = parse_qs(parsed.query, keep_blank_values=True)
    changed = False
    cert_values = query.get("sslrootcert")
    if cert_values:
        current = cert_values[0]
        if current and not Path(current).is_absolute():
            resolved = (_BACKEND_ROOT / current).resolve().as_posix()
            query["sslrootcert"] = [resolved]
            changed = True
    if not changed:
        return url
    parts: list[str] = []
    for key, values in query.items():
        for value in values:
            parts.append(f"{key}={value}")
    normalized_query = "&".join(parts)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.params:
        base = f"{base};{parsed.params}"
    if normalized_query:
        base = f"{base}?{normalized_query}"
    if parsed.fragment:
        base = f"{base}#{parsed.fragment}"
    return base


_load_backend_env()
os.environ.setdefault("APP_DATABASE_SSL_CA", "")

database_url = os.environ.get("APP_DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "APP_DATABASE_URL is not configured. Set it to the dev PostgreSQL DSN before running tests."
    )

os.environ["APP_DATABASE_URL"] = _normalize_database_url(database_url)

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


def make_jwt(sub: str, role: str = "user", audience: str | None = None) -> str:
    _ensure_backend_on_path()
    from packages.core.config import load_settings

    settings = load_settings()
    role_value = str(role).lower()
    aud = audience
    if aud is None:
        if role_value in {"admin", "moderator", "editor"}:
            aud = "admin"
        elif role_value == "support":
            aud = "ops"
        else:
            aud = "public"
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + 600}
    if aud:
        payload["audience"] = aud
    return jwt.encode(
        payload,
        key=settings.auth_jwt_secret.get_secret_value(),
        algorithm=settings.auth_jwt_algorithm,
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
