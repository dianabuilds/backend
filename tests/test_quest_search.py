import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.workspaces.infrastructure.models import Workspace


@pytest.mark.asyncio
async def test_search_and_filter_quests(
    client: AsyncClient, db_session: AsyncSession, test_user
):
    now = datetime.utcnow()
    ws = Workspace(name="ws", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    q1 = Quest(
        title="Lost Crown",
        subtitle="Adventure",
        description="Find the lost crown in the ancient ruins",
        tags=["adventure", "exploration"],
        author_id=test_user.id,
        is_draft=False,
        price=50,
        published_at=now,
        workspace_id=ws.id,
    )
    q2 = Quest(
        title="Haunted Cave",
        description="Spooky and scary",
        tags=["horror"],
        author_id=test_user.id,
        price=100,
        is_premium_only=True,
        is_draft=False,
        published_at=now,
        workspace_id=ws.id,
    )
    q3 = Quest(
        title="Free Forest",
        description="Wander freely",
        tags=["exploration"],
        author_id=test_user.id,
        is_draft=False,
        published_at=now,
        workspace_id=ws.id,
    )

    db_session.add_all([q1, q2, q3])
    await db_session.commit()

    resp = await client.get("/quests/search", params={"q": "crown"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1 and data[0]["title"] == "Lost Crown"

    resp = await client.get("/quests/search", params={"tags": "exploration"})
    assert resp.status_code == 200
    data = resp.json()
    titles = {d["title"] for d in data}
    assert titles == {"Lost Crown", "Free Forest"}

    resp = await client.get("/quests/search", params={"free_only": "true"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1 and data[0]["title"] == "Free Forest"

    resp = await client.get("/quests/search", params={"premium_only": "true"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1 and data[0]["title"] == "Haunted Cave"
