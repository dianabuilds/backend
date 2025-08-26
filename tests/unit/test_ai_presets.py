import importlib
import sys
import types
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package is importable as in existing tests
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Provide a minimal stub for app.security to avoid heavy imports during tests
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}
security_stub.auth_user = lambda: None
security_stub.require_ws_editor = lambda *a, **k: None
security_stub.require_ws_owner = lambda *a, **k: None
sys.modules.setdefault("app.security", security_stub)

from fastapi import HTTPException

from app.core.preview import PreviewContext
from app.domains.ai.infrastructure.models.generation_models import GenerationJob
from app.domains.ai.services.generation import (
    enqueue_generation_job,
    process_next_generation_job,
)
from app.domains.workspaces.api import put_ai_presets
from app.domains.workspaces.infrastructure.models import Workspace
from app.domains.ai.infrastructure.models.ai_settings import AISettings
from app.schemas.workspaces import WorkspaceSettings


@pytest.mark.asyncio
async def test_put_ai_presets_invalid() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()

        with pytest.raises(HTTPException) as exc:
            await put_ai_presets(ws.id, {"temperature": "hot"}, None, session)
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_generation_uses_workspace_presets(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.metadata.create_all)
        await conn.run_sync(GenerationJob.__table__.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        presets = {
            "provider": "workspace-provider",
            "model": "gpt-test",
            "temperature": 0.5,
            "system_prompt": "system",
            "forbidden": ["foo"],
        }
        ws = Workspace(
            id=uuid.uuid4(),
            name="W",
            slug="w",
            owner_user_id=uuid.uuid4(),
            settings_json=WorkspaceSettings(ai_presets=presets).model_dump(),
        )
        session.add(ws)
        await session.commit()

        job = await enqueue_generation_job(
            session,
            created_by=None,
            params={},
            provider=None,
            model=None,
            workspace_id=ws.id,
            reuse=False,
            preview=PreviewContext(),
        )
        await session.commit()

        assert job.provider == "workspace-provider"
        assert job.model == "gpt-test"
        assert job.params["temperature"] == 0.5
        assert job.params["system_prompt"] == "system"
        assert job.params["forbidden"] == ["foo"]

        called = {}

        async def fake_run_full_generation(db, job_arg):
            called["provider"] = job_arg.provider
            called["model"] = job_arg.model
            called["params"] = job_arg.params
            return {}

        from app.domains.ai import pipeline as ai_pipeline

        monkeypatch.setattr(
            ai_pipeline, "run_full_generation", fake_run_full_generation
        )

        await process_next_generation_job(session)

        assert called["provider"] == "workspace-provider"
        assert called["model"] == "gpt-test"
        assert called["params"]["temperature"] == 0.5
        assert called["params"]["system_prompt"] == "system"
        assert called["params"]["forbidden"] == ["foo"]


@pytest.mark.asyncio
async def test_generation_merges_sources_and_logs() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.metadata.create_all)
        await conn.run_sync(GenerationJob.__table__.metadata.create_all)
        await conn.run_sync(AISettings.__table__.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ai = AISettings(provider="openai", model="gpt-global")
        session.add(ai)
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4(), settings_json=WorkspaceSettings(ai_presets={"system_prompt": "ws-system"}).model_dump())
        session.add(ws)
        await session.commit()

        job = await enqueue_generation_job(
            session,
            created_by=None,
            params={"temperature": 0.9},
            provider=None,
            model="explicit-model",
            workspace_id=ws.id,
            reuse=False,
            preview=PreviewContext(),
        )
        await session.commit()

        assert job.model == "explicit-model"
        assert job.provider == "openai"
        assert job.params["temperature"] == 0.9
        assert job.params["system_prompt"] == "ws-system"
        trace = job.logs[0]["applied"]
        assert trace["model"]["source"] == "explicit"
        assert trace["provider"]["source"] == "global"
        assert trace["temperature"]["source"] == "explicit"
        assert trace["system_prompt"]["source"] == "workspace"
