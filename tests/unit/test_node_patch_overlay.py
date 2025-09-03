from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.nodes.dao import NodePatchDAO  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        NodePatch.__table__.c.id_bigint.type = sa.Integer()
        NodePatch.__table__.c.node_id_bigint.type = sa.Integer()
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_overlay_applies_patch_with_single_query(db: AsyncSession) -> None:
    ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
    db.add(ws)
    await db.flush()

    item1 = NodeItem(
        workspace_id=ws.id,
        type="quest",
        status=Status.draft,
        visibility=Visibility.private,
        slug="n1",
        title="old1",
    )
    item2 = NodeItem(
        workspace_id=ws.id,
        type="quest",
        status=Status.draft,
        visibility=Visibility.private,
        slug="n2",
        title="old2",
    )
    db.add_all([item1, item2])
    await db.flush()

    patch = NodePatch(node_id=item1.id, data={"title": "new1"})
    db.add(patch)
    await db.flush()

    queries: list[str] = []

    def count_sql(
        conn, cursor, statement, parameters, context, executemany
    ):  # noqa: ANN001
        if "node_patches" in statement.lower():
            queries.append(statement)

    engine = db.bind.sync_engine
    event.listen(engine, "before_cursor_execute", count_sql)
    try:
        await NodePatchDAO.overlay(db, [item1, item2])
    finally:
        event.remove(engine, "before_cursor_execute", count_sql)

    assert item1.title == "new1"
    assert item2.title == "old2"
    assert len(queries) == 1
