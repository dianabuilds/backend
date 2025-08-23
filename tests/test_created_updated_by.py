import pytest
import pytest_asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.content.models import ContentItem  # noqa: F401
from app.domains.tags.models import Tag  # noqa: F401
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: F401
from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter
from app.domains.nodes.infrastructure.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate
from app.domains.quests.authoring import create_quest, update_quest
from app.schemas.quest import QuestCreate, QuestUpdate
from app.domains.achievements.application.admin_service import AchievementsAdminService
from app.domains.achievements.infrastructure.repositories.achievements_repository import AchievementsRepository
from app.domains.achievements.infrastructure.models.achievement_models import Achievement
from app.domains.worlds.application.worlds_service import WorldsService
from app.domains.worlds.infrastructure.repositories.worlds_repository import WorldsRepository
from app.domains.ai.infrastructure.models.world_models import WorldTemplate, Character
from app.domains.workspaces.infrastructure.models import Workspace


@pytest.mark.asyncio
async def test_created_updated_by_fields(db_session: AsyncSession, test_user, admin_user):
    # create necessary tables
    await db_session.run_sync(lambda s: Workspace.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Node.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Tag.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodeTag.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Achievement.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: WorldTemplate.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Character.__table__.create(s.bind, checkfirst=True))
    from app.domains.quests.infrastructure.models.quest_models import Quest
    await db_session.run_sync(lambda s: Quest.__table__.create(s.bind, checkfirst=True))

    ws = Workspace(id=uuid4(), name="ws", slug="ws", owner_user_id=admin_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    # Node
    repo = NodeRepositoryAdapter(db_session)
    node = await repo.create(NodeCreate(title="n", content={}), test_user.id, ws.id)
    assert node.created_by_user_id == test_user.id
    node = await repo.update(node, NodeUpdate(title="n2"), test_user.id)
    assert node.updated_by_user_id == test_user.id

    # Quest
    quest = await create_quest(db_session, payload=QuestCreate(title="q", nodes=[], custom_transitions={}), author=test_user, workspace_id=ws.id)
    assert quest.created_by_user_id == test_user.id
    quest = await update_quest(db_session, quest_id=quest.id, payload=QuestUpdate(title="q2"), actor=test_user)
    assert quest.updated_by_user_id == test_user.id

    # Achievement
    svc = AchievementsAdminService(AchievementsRepository(db_session))
    ach = await svc.create(db_session, ws.id, {"code": "a1", "title": "A", "condition": {}}, admin_user.id)
    assert ach.created_by_user_id == admin_user.id
    ach = await svc.update(db_session, ws.id, ach.id, {"title": "B"}, admin_user.id)
    assert ach.updated_by_user_id == admin_user.id

    # World & Character
    worlds_svc = WorldsService(WorldsRepository(db_session))
    world = await worlds_svc.create_world(db_session, ws.id, {"title": "W"}, admin_user.id)
    assert world.created_by_user_id == admin_user.id
    world = await worlds_svc.update_world(db_session, ws.id, world.id, {"description": "d"}, admin_user.id)
    assert world.updated_by_user_id == admin_user.id
    character = await worlds_svc.create_character(db_session, world.id, ws.id, {"name": "C"}, admin_user.id)
    assert character.created_by_user_id == admin_user.id
    character = await worlds_svc.update_character(db_session, character.id, ws.id, {"role": "hero"}, admin_user.id)
    assert character.updated_by_user_id == admin_user.id

    # cleanup tables
    await db_session.run_sync(lambda s: Character.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: WorldTemplate.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Achievement.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodeTag.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Tag.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Node.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Quest.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Workspace.__table__.drop(s.bind, checkfirst=True))
