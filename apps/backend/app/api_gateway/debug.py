from __future__ import annotations

from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Header, Request

from domains.platform.iam.security import get_current_user
from packages.core.config import load_settings


def make_router() -> APIRouter:
    router = APIRouter(prefix="/debug", tags=["debug"])

    @router.get("/config")
    async def config(request: Request) -> dict[str, Any]:
        s = load_settings()
        # Only expose non-sensitive hints in non-prod environments
        data: dict[str, Any] = {
            "env": s.env,
            "jwt_algorithm": s.auth_jwt_algorithm,
            "jwt_secret_hint": sha256(str(s.auth_jwt_secret).encode()).hexdigest()[:10],
            "admin_key_present": bool(s.admin_api_key),
            "admin_key_len": (len(s.admin_api_key) if s.admin_api_key else 0),
        }
        return data

    @router.get("/whoami")
    async def whoami(
        request: Request,
        admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    ) -> dict[str, Any]:
        s = load_settings()
        try:
            claims = await get_current_user(request)
        except Exception as e:  # pragma: no cover - purely debug endpoint
            claims = {"error": str(e)}
        return {
            "env": s.env,
            "claims": claims,
            "admin_key_present": bool(s.admin_api_key),
            "admin_key_match": bool(s.admin_api_key) and (admin_key == s.admin_api_key),
        }

    return router
