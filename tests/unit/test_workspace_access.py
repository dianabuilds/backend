import importlib
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.quests.queries import get_for_view
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest.mark.asyncio
async def test_get_for_view_respects_workspace() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        w1 = Workspace(
            id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=uuid.uuid4()
        )
        w2 = Workspace(
            id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=uuid.uuid4()
        )
        q = Quest(
            workspace_id=w1.id,
            title="Quest",
            tags=[],
            author_id=uuid.uuid4(),
            nodes=[],
            custom_transitions=None,
            status=Status.published,
            visibility=Visibility.private,
            created_by_user_id=uuid.uuid4(),
            allow_comments=True,
        )
        session.add_all([w1, w2, q])
        await session.commit()
        await session.refresh(q)
        q.is_draft = False

        user = SimpleNamespace(id=q.author_id, is_premium=False)

        res = await get_for_view(session, slug=q.slug, user=user, workspace_id=w1.id)
        assert res.id == q.id

        with pytest.raises(ValueError):
            await get_for_view(session, slug=q.slug, user=user, workspace_id=w2.id)
