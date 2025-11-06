import uuid

import pytest

from domains.product.content.domain import HomeConfigDraftNotFound, HomeConfigStatus
from domains.product.content.infrastructure.home_config_repository import (
    HomeConfigRepository,
)


@pytest.mark.asyncio()
async def test_create_and_get_draft(repository: HomeConfigRepository) -> None:
    draft = await repository.create_draft(
        "main",
        {"blocks": []},
        actor="alice",
        base_config_id=None,
    )
    assert draft.status is HomeConfigStatus.DRAFT
    fetched = await repository.get_draft("main")
    assert fetched is not None
    assert fetched.id == draft.id
    assert fetched.created_by == "alice"


@pytest.mark.asyncio()
async def test_update_draft(repository: HomeConfigRepository) -> None:
    draft = await repository.create_draft(
        "main",
        {"blocks": []},
        actor="alice",
        base_config_id=None,
    )
    updated = await repository.update_draft(
        draft.id,
        {"blocks": [{"id": "hero", "type": "hero", "enabled": True}]},
        actor="bob",
    )
    assert updated.updated_by == "bob"
    assert updated.data["blocks"][0]["id"] == "hero"


@pytest.mark.asyncio()
async def test_publish_increments_version(repository: HomeConfigRepository) -> None:
    draft = await repository.create_draft(
        "main",
        {"blocks": []},
        actor="alice",
        base_config_id=None,
    )
    assert draft.version == 0
    published = await repository.publish(draft.id, actor="alice")
    assert published.status is HomeConfigStatus.PUBLISHED
    assert published.version == 1
    active = await repository.get_active("main")
    assert active is not None
    assert active.id == published.id


@pytest.mark.asyncio()
async def test_restore_creates_new_draft(repository: HomeConfigRepository) -> None:
    draft = await repository.create_draft(
        "main",
        {"blocks": []},
        actor="alice",
        base_config_id=None,
    )
    published = await repository.publish(draft.id, actor="alice")
    restored = await repository.restore_version("main", published.version, actor="bob")
    assert restored.status is HomeConfigStatus.DRAFT
    assert restored.draft_of == published.id
    assert restored.version == published.version
    assert restored.created_by == "bob"


@pytest.mark.asyncio()
async def test_add_audit_entry(repository: HomeConfigRepository) -> None:
    draft = await repository.create_draft(
        "main",
        {"blocks": []},
        actor="alice",
        base_config_id=None,
    )
    published = await repository.publish(draft.id, actor="alice")
    audit = await repository.add_audit(
        config_id=published.id,
        version=published.version,
        action="publish",
        actor="alice",
        actor_team="content",
        comment="Initial release",
        data={"blocks": []},
        diff=[{"op": "add", "path": "/blocks", "value": []}],
    )
    assert audit.config_id == published.id
    assert audit.version == published.version
    assert audit.action == "publish"
    assert audit.actor_team == "content"
    assert audit.comment == "Initial release"
    assert audit.diff == [{"op": "add", "path": "/blocks", "value": []}]


@pytest.mark.asyncio()
async def test_list_history_returns_entries(repository: HomeConfigRepository) -> None:
    draft = await repository.create_draft(
        "main",
        {"blocks": []},
        actor="alice",
        base_config_id=None,
    )
    await repository.publish(draft.id, actor="alice")
    draft_2 = await repository.create_draft(
        "main",
        {"blocks": [{"id": "hero", "type": "hero", "enabled": True}]},
        actor="bob",
        base_config_id=None,
    )
    published_2 = await repository.publish(draft_2.id, actor="bob")
    history = await repository.list_history("main", limit=10)
    assert history
    assert history[0].config.id == published_2.id
    assert history[0].actor == "bob"
    assert history[0].config.version == published_2.version
    assert len(history) >= 2


@pytest.mark.asyncio()
async def test_update_missing_draft(repository: HomeConfigRepository) -> None:
    with pytest.raises(HomeConfigDraftNotFound):
        await repository.update_draft(
            uuid.uuid4(),
            {"blocks": []},
            actor="ghost",
        )
