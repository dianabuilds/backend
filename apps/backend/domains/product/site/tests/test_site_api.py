from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.backend.app.api_gateway.routers import get_container
from domains.product.site.api.admin_http import get_site_service, make_router
from domains.product.site.application import SiteService
from domains.product.site.domain import PageReviewStatus, PageType


@pytest_asyncio.fixture()
async def api_client(service: SiteService):
    app = FastAPI()
    router = make_router()
    app.include_router(router)

    async def override_site_service() -> SiteService:
        return service

    async def allow_dependency(request=None) -> None:
        return None

    app.dependency_overrides[get_site_service] = override_site_service
    for route in router.routes:
        for dependency in route.dependant.dependencies:
            app.dependency_overrides.setdefault(dependency.call, allow_dependency)

    dummy_container = SimpleNamespace(
        navigation_service=None,
        nodes_service=None,
        settings=SimpleNamespace(embedding_enabled=False),
    )
    app.dependency_overrides[get_container] = lambda: dummy_container

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield client
    finally:
        await client.aclose()


@pytest.mark.asyncio()
async def test_validate_page_draft_endpoint_success(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/validate",
        page_type=PageType.LANDING,
        title="Validate",
        locale="ru",
        owner=None,
    )
    response = await api_client.post(
        f"/v1/site/pages/{page.id}/draft/validate",
        json={
            "data": {
                "blocks": [
                    {"id": "hero-1", "type": "hero", "enabled": True},
                    {"id": "list-1", "type": "nodes_carousel", "enabled": True},
                ]
            },
            "meta": {"title": "Preview"},
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["valid"] is True
    assert payload["data"]["blocks"][0]["id"] == "hero-1"
    assert payload["meta"]["title"] == "Preview"


@pytest.mark.asyncio()
async def test_validate_page_draft_endpoint_errors(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/validate-errors",
        page_type=PageType.LANDING,
        title="Validate errors",
        locale="ru",
        owner=None,
    )
    response = await api_client.post(
        f"/v1/site/pages/{page.id}/draft/validate",
        json={
            "data": {
                "blocks": [
                    {"id": "hero-1", "type": "hero", "enabled": True},
                    {"id": "hero-1", "type": "hero", "enabled": True},
                ]
            }
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["valid"] is False
    assert payload["code"] == "site_page_validation_failed"
    assert "hero-1" in payload["errors"]["blocks"]


@pytest.mark.asyncio()
async def test_diff_page_draft_endpoint(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/diff-api",
        page_type=PageType.LANDING,
        title="Diff API",
        locale="ru",
        owner=None,
    )
    initial = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True},
            ]
        },
        meta={"title": "First"},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=initial.version,
        actor=None,
    )
    await service.publish_page(page_id=page.id, actor=None, comment=None, diff=None)
    draft_after_publish = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Updated"},
                {"id": "promo-1", "type": "recommendations", "enabled": True},
            ]
        },
        meta={"title": "Second"},
        comment=None,
        review_status=PageReviewStatus.PENDING,
        expected_version=draft_after_publish.version,
        actor=None,
    )
    response = await api_client.get(f"/v1/site/pages/{page.id}/draft/diff")
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["draft_version"] >= draft_after_publish.version + 1
    assert payload["published_version"] == 1
    diff_signatures = {
        (entry.get("type"), entry.get("blockId") or entry.get("field"), entry.get("change"))
        for entry in payload["diff"]
    }
    assert ("block", "hero-1", "updated") in diff_signatures
    assert ("block", "promo-1", "added") in diff_signatures


@pytest.mark.asyncio()
async def test_preview_page_endpoint(
    service: SiteService,
    api_client: AsyncClient,
):
    page = await service.create_page(
        slug="/preview-api",
        page_type=PageType.LANDING,
        title="Preview API",
        locale="ru",
        owner=None,
    )
    draft = await service.get_page_draft(page.id)
    await service.save_page_draft(
        page_id=page.id,
        payload={
            "blocks": [
                {"id": "hero-1", "type": "hero", "enabled": True, "title": "Hero"},
            ]
        },
        meta={"title": "Preview API"},
        comment=None,
        review_status=PageReviewStatus.NONE,
        expected_version=draft.version,
        actor=None,
    )
    response = await api_client.post(
        f"/v1/site/pages/{page.id}/preview",
        json={
            "layouts": ["mobile"],
        },
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["page"]["slug"] == "/preview-api"
    assert payload["version_mismatch"] is False
    assert "mobile" in payload["layouts"]
    mobile_layout = payload["layouts"]["mobile"]
    assert mobile_layout["data"]["blocks"][0]["id"] == "hero-1"


@pytest.mark.asyncio()
async def test_block_preview_endpoint(
    api_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = {
        "block": "recommendations",
        "locale": "ru",
        "source": "live",
        "fetched_at": "2025-10-26T11:00:00Z",
        "items": [{"title": "Sample", "href": "/n/sample"}],
        "meta": {"mode": "site_preview"},
    }

    async def fake_preview(container, block_id, *, locale, limit):
        assert block_id == "recommendations"
        assert locale == "ru"
        assert limit == 5
        return sample

    monkeypatch.setattr(
        "domains.product.site.api.admin_http.build_block_preview",
        fake_preview,
    )

    response = await api_client.get(
        "/v1/site/blocks/recommendations/preview?locale=ru&limit=5",
    )
    assert response.status_code == 200
    assert response.json() == sample
