from types import SimpleNamespace

import pytest

from domains.product.content.api.home_http import _build_node_data_service
from domains.product.nodes.application.ports import NodeDTO
from domains.product.nodes.domain.results import NodeView


class _FakeNodeService:
    def __init__(self, dto: NodeDTO) -> None:
        self._dto = dto

    async def _repo_get_async(self, node_id: int):
        if int(node_id) == int(self._dto.id):
            return self._dto
        return None

    async def _repo_get_by_slug_async(self, slug: str):
        if slug == self._dto.slug:
            return self._dto
        return None

    def _to_view(self, dto: NodeDTO) -> NodeView:
        return NodeView(
            id=int(dto.id),
            slug=str(dto.slug),
            author_id=str(dto.author_id),
            title=dto.title,
            tags=list(dto.tags),
            is_public=bool(dto.is_public),
            status=dto.status,
            publish_at=dto.publish_at,
            unpublish_at=dto.unpublish_at,
            content_html=dto.content_html,
            cover_url=dto.cover_url,
            embedding=list(dto.embedding) if dto.embedding is not None else None,
            views_count=int(dto.views_count or 0),
            reactions_like_count=int(dto.reactions_like_count or 0),
            comments_disabled=bool(dto.comments_disabled),
            comments_locked_by=dto.comments_locked_by,
            comments_locked_at=dto.comments_locked_at,
        )


@pytest.mark.asyncio()
async def test_node_data_service_fetch_many_uses_async_repo() -> None:
    dto = NodeDTO(
        id=101,
        slug="hero-1",
        author_id="user-1",
        title="Hero",
        tags=["featured"],
        is_public=True,
        status="published",
        publish_at="2025-10-11T00:00:00Z",
        unpublish_at=None,
        content_html="<p>hello</p>",
        cover_url="https://cdn.example/hero.png",
        embedding=None,
        views_count=12,
        reactions_like_count=4,
        comments_disabled=False,
        comments_locked_by=None,
        comments_locked_at=None,
    )
    container = SimpleNamespace(nodes_service=_FakeNodeService(dto))

    service = _build_node_data_service(container)

    items = await service.fetch_many([dto.slug])

    assert items
    card = items[0]
    assert card["id"] == str(dto.id)
    assert card["slug"] == dto.slug
    assert card["title"] == dto.title
    assert card["views"] == dto.views_count
    assert card["reactions"] == dto.reactions_like_count
