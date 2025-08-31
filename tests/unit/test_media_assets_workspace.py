import importlib
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.db.base import Base  # noqa: E402
from app.domains.media.dao import MediaAssetDAO  # noqa: E402
from app.domains.media.models import MediaAsset  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402


def test_media_asset_list_scoped_by_workspace() -> None:
    async def _run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            w1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user.id)
            w2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user.id)
            a1 = MediaAsset(workspace_id=w1.id, url="u1", type="image/png")
            a2 = MediaAsset(workspace_id=w2.id, url="u2", type="image/png")
            session.add_all([user, w1, w2, a1, a2])
            await session.commit()

            res1 = await MediaAssetDAO.list(session, workspace_id=w1.id)
            res2 = await MediaAssetDAO.list(session, workspace_id=w2.id)
            assert [a.workspace_id for a in res1] == [w1.id]
            assert [a.workspace_id for a in res2] == [w2.id]

    import asyncio

    asyncio.run(_run())
