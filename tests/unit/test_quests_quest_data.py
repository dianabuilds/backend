import importlib
import sys
import types
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.api import deps  # noqa: E402
from app.domains.quests.api.quests_router import router as quests_router  # noqa: E402


@pytest.mark.asyncio
async def test_post_put_forbid_quest_data() -> None:
    app = FastAPI()
    app.include_router(quests_router)

    # Override dependencies
    app.dependency_overrides[deps.get_current_user] = lambda: types.SimpleNamespace(
        id=uuid.uuid4()
    )

    async def fake_db():
        yield None

    app.dependency_overrides[deps.get_db] = fake_db
    app.dependency_overrides[deps.get_preview_context] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/quests?workspace_id=00000000-0000-0000-0000-000000000000",
            json={"title": "q", "quest_data": {}},
        )
        assert resp.status_code == 422
        assert "quest_data" in resp.text

        resp = await ac.put(
            f"/quests/{uuid.uuid4()}?workspace_id=00000000-0000-0000-0000-000000000000",
            json={"quest_data": {}},
        )
        assert resp.status_code == 422
        assert "quest_data" in resp.text


@pytest.mark.asyncio
async def test_get_quest_includes_quest_data(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.include_router(quests_router)

    app.dependency_overrides[deps.get_current_user] = lambda: types.SimpleNamespace(
        id=uuid.uuid4()
    )

    async def fake_db():
        yield None

    app.dependency_overrides[deps.get_db] = fake_db

    quest_id = uuid.uuid4()
    quest = types.SimpleNamespace(
        id=quest_id,
        slug="quest-slug",
        author_id=uuid.uuid4(),
        is_draft=False,
        published_at=None,
        created_at=datetime.utcnow(),
        created_by_user_id=None,
        updated_by_user_id=None,
        title="Quest",
        subtitle=None,
        description=None,
        cover_image=None,
        tags=[],
        price=None,
        is_premium_only=False,
        entry_node_id=None,
        nodes=[],
        custom_transitions=None,
        allow_comments=True,
        structure=None,
        length=None,
        tone=None,
        genre=None,
        locale=None,
        cost_generation=None,
    )

    async def fake_get_for_view(db, slug, user, workspace_id):
        return quest

    monkeypatch.setattr("app.domains.quests.queries.get_for_view", fake_get_for_view)

    version = types.SimpleNamespace(
        id=uuid.uuid4(),
        quest_id=quest_id,
        number=1,
        status="released",
        created_at=datetime.utcnow(),
        created_by=None,
        released_at=None,
        released_by=None,
        parent_version_id=None,
        meta={},
    )

    async def fake_latest_version(db, quest_id):
        return version

    monkeypatch.setattr(
        "app.domains.quests.api.quests_router.latest_version", fake_latest_version
    )

    async def fake_get_version_graph(self, db, version_id):
        return (version, [], [])

    monkeypatch.setattr(
        "app.domains.quests.application.editor_service.EditorService.get_version_graph",
        fake_get_version_graph,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/quests/{quest.slug}?workspace_id=00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["quest_data"]["steps"] == []
        assert body["quest_data"]["transitions"] == []
