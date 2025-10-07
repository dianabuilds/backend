from __future__ import annotations

import pytest
from fastapi import HTTPException

from domains.product.nodes.application.use_cases.catalog import (
    DevBlogService,
    NodeCatalogService,
)


class StubDevBlogRepository:
    async def fetch_page(self, engine, *, limit: int, offset: int):
        items = [
            {
                "id": 1,
                "slug": "hello",
                "summary": "hi",
                "publish_at": None,
                "updated_at": None,
            },
            {
                "id": 2,
                "slug": "world",
                "summary": "bye",
                "publish_at": None,
                "updated_at": None,
            },
        ]
        return items[:limit], 5


class StubNodesService:
    def __init__(self, view=None):
        self.view = view
        self._ref_called = False

    async def _repo_get_async(self, node_id: int):
        self._ref_called = True
        return type("DTO", (), {"id": node_id}) if self.view else None

    async def _repo_get_by_slug_async(self, slug: str):
        return type("DTO", (), {"id": 1}) if self.view else None

    def _to_view(self, dto):
        return self.view

    def get_by_slug(self, slug: str):
        return self.view


class StubView:
    def __init__(self, *, is_public: bool = True, author_id: str = "user-1"):
        self.id = 1
        self.slug = "slug"
        self.author_id = author_id
        self.title = "title"
        self.tags = ["python"]
        self.is_public = is_public
        self.status = "published"
        self.publish_at = None
        self.unpublish_at = None
        self.content_html = "<p>hello</p>"
        self.cover_url = None
        self.embedding = None
        self.views_count = 0
        self.reactions_like_count = 0
        self.comments_disabled = False
        self.comments_locked_by = None
        self.comments_locked_at = None


@pytest.mark.asyncio
async def test_dev_blog_service_happy_path():
    async def engine_factory():
        return object()

    service = DevBlogService(
        engine_factory=engine_factory, repository=StubDevBlogRepository()
    )
    result = await service.list_posts(limit=2, offset=0)
    assert result["total"] == 5
    assert result["has_next"] is True
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_dev_blog_service_missing_engine():
    async def engine_factory():
        return None

    service = DevBlogService(
        engine_factory=engine_factory, repository=StubDevBlogRepository()
    )
    with pytest.raises(HTTPException) as exc:
        await service.list_posts(limit=2, offset=0)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_node_catalog_service_allows_public_view():
    svc = NodeCatalogService(nodes_service=StubNodesService(view=StubView()))
    result = await svc.get_by_ref("1", claims={"sub": "user-2"})
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_node_catalog_service_denies_private_view_for_other_user():
    view = StubView(is_public=False, author_id="owner")
    svc = NodeCatalogService(nodes_service=StubNodesService(view=view))
    with pytest.raises(HTTPException) as exc:
        await svc.get_by_ref("1", claims={"sub": "intruder"})
    assert exc.value.status_code == 404


def test_node_catalog_service_get_by_slug():
    view = StubView()
    svc = NodeCatalogService(nodes_service=StubNodesService(view=view))
    result = svc.get_by_slug("slug", claims={"sub": "user-1"})
    assert result["slug"] == "slug"
