import pytest
import pytest_asyncio
import sqlalchemy as sa

from domains.product.content.application import HomeConfigService
from domains.product.content.domain import (
    HomeConfigDuplicateBlockError,
    HomeConfigSchemaError,
    HomeConfigStatus,
)


@pytest_asyncio.fixture()
async def service(repository) -> HomeConfigService:
    return HomeConfigService(repository=repository)


@pytest.mark.asyncio()
async def test_save_draft_creates_new(service: HomeConfigService) -> None:
    draft = await service.save_draft(
        "main",
        {"blocks": [{"id": "hero", "type": "hero", "enabled": True}]},
        actor="alice",
    )
    assert draft.status is HomeConfigStatus.DRAFT
    assert draft.created_by == "alice"


@pytest.mark.asyncio()
async def test_save_draft_rejects_duplicate_blocks(service: HomeConfigService) -> None:
    with pytest.raises(HomeConfigDuplicateBlockError):
        await service.save_draft(
            "main",
            {
                "blocks": [
                    {"id": "hero", "type": "hero", "enabled": True},
                    {"id": "hero", "type": "hero", "enabled": True},
                ]
            },
            actor="alice",
        )


@pytest.mark.asyncio()
async def test_save_draft_invalid_schema(service: HomeConfigService) -> None:
    with pytest.raises(HomeConfigSchemaError):
        await service.save_draft("main", {"invalid": True}, actor="alice")


@pytest.mark.asyncio()
async def test_publish_creates_audit(service: HomeConfigService, engine) -> None:
    await service.save_draft(
        "main",
        {"blocks": [{"id": "hero", "type": "hero", "enabled": True}]},
        actor="alice",
    )
    published = await service.publish("main", actor="alice", actor_team="content")
    assert published.status is HomeConfigStatus.PUBLISHED
    async with engine.connect() as conn:
        result = await conn.execute(
            sa.text("SELECT action, actor, actor_team, diff FROM home_config_audits")
        )
        rows = result.mappings().all()
    assert any(row["action"] == "publish" and row["actor"] == "alice" for row in rows)
    assert any(row["actor_team"] == "content" for row in rows)
    assert any(row.get("diff") for row in rows)


@pytest.mark.asyncio()
async def test_get_history_returns_latest_entry(service: HomeConfigService) -> None:
    await service.save_draft(
        "main",
        {"blocks": [{"id": "hero", "type": "hero", "enabled": True}]},
        actor="alice",
    )
    await service.publish("main", actor="alice")
    history = await service.get_history("main")
    assert history
    assert history[0].config.version == 1
    assert history[0].actor == "alice"
