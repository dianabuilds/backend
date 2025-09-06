from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from httpx import ASGITransport, AsyncClient

# Stub external dependencies required during import
sys.modules["app.api.deps"] = types.SimpleNamespace(get_current_user_optional=None)
sys.modules["app.domains.admin.application.feature_flag_service"] = types.SimpleNamespace(
    FeatureFlagKey=None, get_effective_flags=None
)
sys.modules["app.domains.users.infrastructure.models.user"] = types.SimpleNamespace(User=object)
sys.modules["app.providers.db.session"] = types.SimpleNamespace(get_db=lambda: None)

base = Path(__file__).resolve().parents[2] / "apps/backend"
spec = importlib.util.spec_from_file_location("admin_override", base / "app/api/admin_override.py")
admin_override = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin_override)
AdminOverrideBannerMiddleware = admin_override.AdminOverrideBannerMiddleware


@pytest.mark.asyncio
async def test_warning_banner_when_override_active():
    app = FastAPI()
    app.add_middleware(AdminOverrideBannerMiddleware)

    async def enable_override(request: Request):
        request.state.admin_override = True

    @app.get("/node", dependencies=[Depends(enable_override)])
    async def node(request: Request) -> dict:
        if not getattr(request.state, "admin_override", False):
            raise HTTPException(status_code=403)
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/node")
    assert resp.status_code == 200
    assert resp.json()["warning_banner"] == "Admin override active"
