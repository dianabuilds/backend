from __future__ import annotations

from uuid import uuid4

from domains.product.nodes.domain.results import NodeView
from tests.conftest import add_auth, make_jwt


def test_nodes_list_returns_items(app_client):
    uid = str(uuid4())
    token = make_jwt(uid)
    add_auth(app_client, token)

    container = app_client.app.state.container
    original_list = container.nodes_service.list_by_author

    def _fake_list(author_id: str, *, limit: int = 50, offset: int = 0):
        assert author_id == uid
        return [
            NodeView(
                id=101,
                slug="demo-node",
                author_id=uid,
                title="Demo Node",
                tags=["demo"],
                is_public=True,
                status="published",
                publish_at=None,
                unpublish_at=None,
                content_html="<p>demo</p>",
                cover_url=None,
                embedding=None,
                views_count=1,
                reactions_like_count=0,
                comments_disabled=False,
                comments_locked_by=None,
                comments_locked_at=None,
            )
        ]

    container.nodes_service.list_by_author = _fake_list
    try:
        response = app_client.get("/v1/nodes")
    finally:
        container.nodes_service.list_by_author = original_list

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"], "expected at least one node"
    node = body["items"][0]
    assert node["author_id"] == uid
    assert node["id"] == 101
    assert node["title"] == "Demo Node"
