from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

import httpx
import jwt

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "apps" / "backend"
for candidate in (_REPO_ROOT, _BACKEND_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

APP_IMPORT_ERROR: str | None
try:
    from apps.backend.app.api_gateway.main import app as _app
except Exception as exc:  # pragma: no cover - defensive baseline logging
    APP_IMPORT_ERROR = f"{exc.__class__.__name__}: {exc}"
    _app = None
else:
    APP_IMPORT_ERROR = None

app: Any | None = _app

load_settings: Callable[[], Any] | None
try:
    from packages.core.config import load_settings as _load_settings
except Exception:  # pragma: no cover - no settings available
    load_settings = None
else:
    load_settings = _load_settings


def _make_jwt(sub: str, role: str) -> str:
    if load_settings is None:
        return ""
    settings = load_settings()
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + 600}
    return jwt.encode(
        payload,
        key=settings.auth_jwt_secret.get_secret_value(),
        algorithm=settings.auth_jwt_algorithm,
    )


async def _measure(
    client: httpx.AsyncClient,
    *,
    name: str,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json_body: Any | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = await client.request(method, url, headers=headers, json=json_body)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return {
            "name": name,
            "method": method,
            "url": url,
            "status": None,
            "latency_ms": round(elapsed_ms, 2),
            "error": str(exc),
        }

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    result: dict[str, Any] = {
        "name": name,
        "method": method,
        "url": url,
        "status": response.status_code,
        "latency_ms": round(elapsed_ms, 2),
    }
    if response.status_code >= 400:
        body = response.text
        result["error"] = body[:400]
    return result


async def _benchmark() -> list[dict[str, Any]]:
    if app is None or load_settings is None:
        error = APP_IMPORT_ERROR or "FastAPI app not available"
        return [
            {
                "name": "nodes:list",
                "method": "GET",
                "url": "/v1/nodes",
                "status": None,
                "latency_ms": 0.0,
                "error": error,
            },
            {
                "name": "moderation:cases",
                "method": "GET",
                "url": "/v1/moderation/cases",
                "status": None,
                "latency_ms": 0.0,
                "error": error,
            },
        ]

    settings = load_settings()
    csrf_header = getattr(settings, "auth_csrf_header_name", "X-CSRF-Token")
    csrf_cookie = getattr(settings, "auth_csrf_cookie_name", "XSRF-TOKEN")
    admin_secret = getattr(settings, "admin_api_key", None)
    admin_key = admin_secret.get_secret_value() if admin_secret else ""

    transport = httpx.ASGITransport(app=app)
    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        if settings:
            client.cookies.set("access_token", _make_jwt("baseline-user", "user"))
            client.cookies.set(csrf_cookie, "csrf-token")
            headers = {csrf_header: "csrf-token"}
        else:
            headers = None
        results.append(
            await _measure(
                client,
                name="nodes:list",
                method="GET",
                url="/v1/nodes",
                headers=headers,
            )
        )

    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        if settings:
            client.cookies.set("access_token", _make_jwt("baseline-admin", "admin"))
            client.cookies.set(csrf_cookie, "csrf-admin")
            headers = {csrf_header: "csrf-admin"}
            if admin_key:
                headers["X-Admin-Key"] = admin_key
        else:
            headers = None
        results.append(
            await _measure(
                client,
                name="moderation:cases",
                method="GET",
                url="/v1/moderation/cases",
                headers=headers,
            )
        )

    return results


def main() -> None:
    results = asyncio.run(_benchmark())
    output_path = _REPO_ROOT / "var" / "api-benchmarks.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
