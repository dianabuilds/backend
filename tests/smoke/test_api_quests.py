from __future__ import annotations

from uuid import uuid4

from tests.conftest import add_auth, make_jwt


def test_quests_create_get_and_update_tags(app_client):
    uid = str(uuid4())
    tok = make_jwt(uid)
    add_auth(app_client, tok)

    # Create quest
    created = app_client.post(
        "/v1/quests",
        json={
            "title": "My Quest",
            "description": "desc",
            "tags": ["alpha", "beta"],
            "is_public": True,
        },
    )
    assert created.status_code == 200, created.text
    qid = created.json()["id"]

    # Get quest
    r = app_client.get(f"/v1/quests/{qid}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["author_id"] == uid
    assert set(body["tags"]) == {"alpha", "beta"}

    # Update tags
    upd = app_client.put(f"/v1/quests/{qid}/tags", json={"tags": ["beta", "gamma"]})
    assert upd.status_code == 200, upd.text
    assert set(upd.json()["tags"]) == {"beta", "gamma"}
