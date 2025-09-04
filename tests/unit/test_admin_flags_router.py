import importlib
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.admin.api.flags_router import update_flag  # noqa: E402
from app.schemas.flags import FeatureFlagUpdateIn  # noqa: E402


@pytest.mark.asyncio
async def test_update_flag_requires_data():
    req = Request({"type": "http"})
    with pytest.raises(HTTPException) as exc:
        await update_flag(
            key="test",
            body=FeatureFlagUpdateIn(),
            request=req,
            current=types.SimpleNamespace(id="1"),
            db=None,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 400
    assert "value" in exc.value.detail
