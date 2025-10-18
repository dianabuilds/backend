from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import get_current_user
from domains.product.nodes.api.public.catalog import register_catalog_routes
from domains.product.nodes.application.ports import NodeDTO
from domains.product.nodes.domain.results import NodeView


class StubNodeService:
    def __init__(self, views: list[NodeView], dto_map: dict[int, NodeDTO]) -> None:
        self._views = views
        self._dto_map = dto_map

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0):
        assert limit > 0
        assert offset >= 0
        return [view for view in self._views if view.author_id == author_id]

    async def _repo_get_async(self, node_id: int):
        return self._dto_map.get(int(node_id))

    async def _repo_get_by_slug_async(self, slug: str):
        for dto in self._dto_map.values():
            if dto.slug == slug:
                return dto
        return None

    def get_by_slug(self, slug: str):
        for view in self._views:
            if view.slug == slug:
                return view
        raise KeyError(slug)

    def _to_view(self, dto: NodeDTO) -> NodeView:
        return NodeView(
            id=dto.id,
            slug=dto.slug,
            author_id=dto.author_id,
            title=dto.title,
            tags=list(dto.tags),
            is_public=dto.is_public,
            status=dto.status,
            publish_at=dto.publish_at,
            unpublish_at=dto.unpublish_at,
            content_html=dto.content_html,
            cover_url=dto.cover_url,
            embedding=dto.embedding,
            views_count=dto.views_count,
            reactions_like_count=dto.reactions_like_count,
            comments_disabled=dto.comments_disabled,
            comments_locked_by=dto.comments_locked_by,
            comments_locked_at=dto.comments_locked_at,
        )


def _build_app(service: StubNodeService, current_user: dict[str, str]) -> TestClient:
    app = FastAPI()
    router = APIRouter(prefix="/v1/nodes")
    register_catalog_routes(router)
    app.include_router(router)

    app.dependency_overrides[get_container] = lambda: SimpleNamespace(
        nodes_service=service
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    return TestClient(app)


def _node_entities(
    owner_id: str, *, is_public: bool = True
) -> tuple[NodeView, NodeDTO]:
    view = NodeView(
        id=900,
        slug="integration-node",
        author_id=owner_id,
        title="Integration Node",
        tags=["integration", "hot-path"],
        is_public=is_public,
        status="published" if is_public else "draft",
        publish_at=None,
        unpublish_at=None,
        content_html="<p>Integration content</p>",
        cover_url=None,
        embedding=None,
        views_count=0,
        reactions_like_count=0,
        comments_disabled=False,
        comments_locked_by=None,
        comments_locked_at=None,
    )
    dto = NodeDTO(
        id=view.id,
        slug=view.slug,
        author_id=view.author_id,
        title=view.title,
        tags=list(view.tags),
        is_public=view.is_public,
        status=view.status,
        publish_at=view.publish_at,
        unpublish_at=view.unpublish_at,
        content_html=view.content_html,
        cover_url=view.cover_url,
        embedding=None,
        views_count=view.views_count,
        reactions_like_count=view.reactions_like_count,
        comments_disabled=view.comments_disabled,
        comments_locked_by=view.comments_locked_by,
        comments_locked_at=view.comments_locked_at,
    )
    return view, dto


def test_nodes_list_and_detail_flow() -> None:
    owner_id = str(uuid4())
    view, dto = _node_entities(owner_id)

    service = StubNodeService([view], {dto.id: dto})
    current_user = {"sub": owner_id}
    client = _build_app(service, current_user)

    list_response = client.get("/v1/nodes")
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    items = body.get("items") or []
    found = next((item for item in items if item["id"] == dto.id), None)
    assert found is not None
    assert found["author_id"] == owner_id

    detail_response = client.get(f"/v1/nodes/{dto.id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["id"] == dto.id
    assert detail["slug"] == dto.slug
    assert detail["tags"] == list(dto.tags)


def test_nodes_private_visibility_rules() -> None:
    owner_id = str(uuid4())
    outsider_id = str(uuid4())
    _, private_dto = _node_entities(owner_id, is_public=False)

    service = StubNodeService([], {private_dto.id: private_dto})
    current_user = {"sub": outsider_id}
    client = _build_app(service, current_user)

    forbidden = client.get(f"/v1/nodes/{private_dto.id}")
    assert forbidden.status_code == 404

    current_user["sub"] = owner_id
    allowed = client.get(f"/v1/nodes/{private_dto.id}")
    assert allowed.status_code == 200, allowed.text
    payload = allowed.json()
    assert payload["id"] == private_dto.id
    assert payload["title"] == private_dto.title
