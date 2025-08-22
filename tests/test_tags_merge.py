import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.core.security import create_access_token
from app.db.session import db_session
from app.domains.tags.infrastructure.models.tag_models import Tag
from app.domains.users.infrastructure.models.user import User


@pytest.mark.asyncio
async def test_tags_merge_dryrun_ok(client: AsyncClient, admin_user: User):
    # Подготовим два тега напрямую в базе
    async with db_session() as session:
        t1 = Tag(id=uuid4(), slug="tag-a", name="Tag A")
        t2 = Tag(id=uuid4(), slug="tag-b", name="Tag B")
        session.add_all([t1, t2])

    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    body = {"from_id": str(t1.id), "to_id": str(t2.id), "dryRun": True}
    resp = await client.post("/admin/tags2/merge", headers=headers, json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["from"]["id"] == str(t1.id)
    assert data["to"]["id"] == str(t2.id)
    assert "content_touched" in data
