import uuid
import sqlalchemy as sa
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.domains.nodes.models import NodeItem
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.models import Tag
from app.schemas.nodes_common import NodeType, Status
from app.validation import run_validators


@pytest.mark.asyncio
async def test_validation_checklist_reports_errors_and_warnings():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(Node.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Existing node with the same slug to trigger uniqueness error
        await session.execute(
            Node.__table__.insert().values(
                id=str(uuid.uuid4()),
                workspace_id=str(uuid.uuid4()),
                slug="dup",  # conflicting slug
                title="",  # Node model has title nullable
                content={},
                author_id=str(uuid.uuid4()),
            )
        )
        await session.commit()

        node = NodeItem(
            id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            type=NodeType.article.value,
            slug="dup",
            title="",  # missing title
            summary="",  # missing summary
            primary_tag_id=None,
            cover_media_id=None,
            status=Status.draft,
            created_by_user_id=uuid.uuid4(),
        )
        session.add(node)
        await session.commit()

        report = await run_validators(NodeType.article.value, node.id, session)
        codes = {i.code for i in report.items}
        assert {
            "slug_exists",
            "title_missing",
            "summary_missing",
            "tag_missing",
            "cover_missing",
            "not_in_review",
        } <= codes
        assert report.errors == 4
        assert report.warnings == 2
